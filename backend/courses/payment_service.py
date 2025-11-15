"""
Razorpay payment processing service
"""

import razorpay
import hmac
import hashlib
from django.conf import settings
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone


class RazorpayService:
    """Wrapper for Razorpay API"""
    
    def __init__(self):
        self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        self.client.set_app_details({"title": "EliteClassroom", "version": "1.0"})
    
    def create_order(self, amount, currency='INR', receipt=None, notes=None):
        """
        Create Razorpay order
        
        Args:
            amount: Amount in smallest currency unit (paise for INR)
            currency: Currency code
            receipt: Receipt ID for reference
            notes: Additional metadata
        
        Returns:
            Order dict with id, amount, currency
        """
        amount_paise = int(amount * 100)  # Convert rupees to paise
        
        data = {
            'amount': amount_paise,
            'currency': currency,
            'receipt': receipt or f"order_{timezone.now().timestamp()}",
            'payment_capture': 1  # Auto-capture after authorization
        }
        
        if notes:
            data['notes'] = notes
        
        order = self.client.order.create(data=data)
        return order
    
    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        Verify payment signature for security
        
        Returns:
            Boolean indicating if signature is valid
        """
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
    
    def capture_payment(self, payment_id, amount, currency='INR'):
        """
        Manually capture a payment (if auto-capture disabled)
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to capture in rupees
            currency: Currency code
        
        Returns:
            Payment dict
        """
        amount_paise = int(amount * 100)
        return self.client.payment.capture(payment_id, amount_paise, {'currency': currency})
    
    def fetch_payment(self, payment_id):
        """Get payment details"""
        return self.client.payment.fetch(payment_id)
    
    def create_refund(self, payment_id, amount=None, notes=None):
        """
        Create refund for a payment
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to refund in rupees (None for full refund)
            notes: Additional metadata
        
        Returns:
            Refund dict
        """
        data = {}
        
        if amount is not None:
            data['amount'] = int(amount * 100)  # Convert to paise
        
        if notes:
            data['notes'] = notes
        
        refund = self.client.payment.refund(payment_id, data)
        return refund
    
    def fetch_refund(self, refund_id):
        """Get refund details"""
        return self.client.refund.fetch(refund_id)
    
    def create_transfer(self, payment_id, amount, account_id, currency='INR', notes=None):
        """
        Transfer funds to linked account (teacher payout)
        
        Args:
            payment_id: Source payment ID
            amount: Amount to transfer in rupees
            account_id: Razorpay account ID of recipient
            currency: Currency code
            notes: Additional metadata
        
        Returns:
            Transfer dict
        """
        amount_paise = int(amount * 100)
        
        data = {
            'account': account_id,
            'amount': amount_paise,
            'currency': currency
        }
        
        if notes:
            data['notes'] = notes
        
        transfer = self.client.payment.transfer(payment_id, data)
        return transfer


class EscrowManager:
    """Manage payment escrow and releases"""
    
    @staticmethod
    def should_release_payment(payment):
        """
        Check if payment should be released from escrow
        
        Conditions:
        - Session is completed
        - Escrow hold period has passed
        - No active disputes
        """
        from .models import Session
        
        if not payment.is_held_in_escrow:
            return False
        
        if payment.released_from_escrow:
            return False
        
        # Check session completion
        if payment.session:
            session = payment.session
            if session.status != 'COMPLETED':
                return False
            
            # Check hold period
            if not payment.escrow_release_date:
                # Set release date if not set
                payment.escrow_release_date = session.ended_at + timedelta(hours=settings.ESCROW_HOLD_HOURS)
                payment.save()
            
            if timezone.now() < payment.escrow_release_date:
                return False
            
            # Check for active disputes/refunds
            if payment.refunds.filter(status__in=['REQUESTED', 'APPROVED', 'PROCESSING']).exists():
                return False
        
        return True
    
    @staticmethod
    def release_payment(payment):
        """
        Release payment from escrow and initiate teacher payout
        
        Returns:
            Payout object or None
        """
        from .models import Payout, TeacherBankAccount
        
        if not EscrowManager.should_release_payment(payment):
            return None
        
        # Get teacher
        teacher = payment.session.teacher if payment.session else payment.course.teacher
        
        # Check if teacher has bank account
        try:
            bank_account = TeacherBankAccount.objects.get(teacher=teacher, is_verified=True)
        except TeacherBankAccount.DoesNotExist:
            # Cannot process payout without verified bank account
            return None
        
        # Create payout
        payout = Payout.objects.create(
            teacher=teacher,
            payment=payment,
            amount=payment.teacher_amount,
            currency=payment.currency,
            razorpay_account_id=bank_account.razorpay_account_id,
            bank_account_number=bank_account.account_number[-4:],  # Last 4 digits only
            bank_ifsc=bank_account.ifsc_code,
            bank_name=bank_account.bank_name,
            status='PENDING'
        )
        
        # Mark payment as released
        payment.released_from_escrow = True
        payment.save()
        
        # Process payout asynchronously (can be Celery task)
        PayoutProcessor.process_payout(payout)
        
        return payout


class PayoutProcessor:
    """Handle teacher payouts"""
    
    @staticmethod
    def process_payout(payout):
        """
        Process payout to teacher's bank account
        
        Args:
            payout: Payout object
        
        Returns:
            Boolean indicating success
        """
        try:
            razorpay_service = RazorpayService()
            
            # Update status
            payout.status = 'PROCESSING'
            payout.processed_at = timezone.now()
            payout.save()
            
            # Create transfer
            transfer = razorpay_service.create_transfer(
                payment_id=payout.payment.razorpay_payment_id,
                amount=float(payout.amount),
                account_id=payout.razorpay_account_id,
                notes={
                    'payout_id': payout.id,
                    'teacher_email': payout.teacher.email
                }
            )
            
            payout.razorpay_transfer_id = transfer['id']
            payout.status = 'COMPLETED'
            payout.completed_at = timezone.now()
            payout.save()
            
            return True
            
        except Exception as e:
            payout.status = 'FAILED'
            payout.failure_reason = str(e)
            payout.save()
            return False
