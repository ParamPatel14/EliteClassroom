from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse
from django.db.models import Sum
from django.conf import settings

from accounts.permissions import IsStudent, IsTeacher
from .models import (
    Payment, Payout, Refund, Invoice, TeacherBankAccount, Session, Course
)
from .serializers import (
    PaymentSerializer, PayoutSerializer, RefundSerializer,
    InvoiceSerializer, TeacherBankAccountSerializer
)
from .payment_service import RazorpayService, EscrowManager, PayoutProcessor
from .invoice_service import InvoiceGenerator


class CreatePaymentOrderView(APIView):
    """Create Razorpay order for session/course booking"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def post(self, request):
        payment_type = request.data.get('payment_type')  # SESSION or COURSE
        item_id = request.data.get('item_id')
        
        if not payment_type or not item_id:
            return Response({'error': 'payment_type and item_id required'}, status=400)
        
        try:
            with transaction.atomic():
                # Get item
                if payment_type == 'SESSION':
                    item = Session.objects.get(id=item_id)
                    amount = item.price
                    teacher = item.teacher
                elif payment_type == 'COURSE':
                    item = Course.objects.get(id=item_id)
                    amount = item.price
                    teacher = item.teacher
                else:
                    return Response({'error': 'Invalid payment_type'}, status=400)
                
                # Calculate fees
                payment = Payment(
                    student=request.user,
                    payment_type=payment_type,
                    amount=amount,
                    currency='INR'
                )
                
                if payment_type == 'SESSION':
                    payment.session_id = item_id
                elif payment_type == 'COURSE':
                    payment.course_id = item_id
                
                payment.calculate_platform_fee()
                
                # Create Razorpay order
                razorpay_service = RazorpayService()
                order = razorpay_service.create_order(
                    amount=float(amount),
                    receipt=f"{payment_type}_{item_id}_{request.user.id}",
                    notes={
                        'student_email': request.user.email,
                        'payment_type': payment_type,
                        'item_id': item_id
                    }
                )
                
                payment.razorpay_order_id = order['id']
                payment.save()
                
                return Response({
                    'order_id': order['id'],
                    'amount': amount,
                    'currency': 'INR',
                    'payment_id': payment.id,
                    'key_id': settings.RAZORPAY_KEY_ID,
                    'platform_fee': payment.platform_fee,
                    'teacher_amount': payment.teacher_amount
                }, status=201)
                
        except (Session.DoesNotExist, Course.DoesNotExist):
            return Response({'error': 'Item not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class VerifyPaymentView(APIView):
    """Verify payment signature and capture payment"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def post(self, request):
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({'error': 'Missing payment details'}, status=400)
        
        try:
            payment = Payment.objects.get(
                razorpay_order_id=razorpay_order_id,
                student=request.user
            )
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=404)
        
        # Verify signature
        razorpay_service = RazorpayService()
        is_valid = razorpay_service.verify_payment_signature(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        )
        
        if not is_valid:
            payment.status = 'FAILED'
            payment.error_description = 'Signature verification failed'
            payment.save()
            return Response({'error': 'Invalid signature'}, status=400)
        
        # Update payment
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = 'CAPTURED'
        payment.captured_at = timezone.now()
        payment.save()
        
        # Update session/course status
        if payment.session:
            payment.session.status = 'CONFIRMED'
            payment.session.is_paid = True
            payment.session.save()
        elif payment.course:
            from .models import Enrollment
            Enrollment.objects.get_or_create(
                student=request.user,
                course=payment.course,
                defaults={'is_paid': True}
            )
        
        # Generate invoice
        InvoiceGenerator.generate_invoice(payment)
        
        return Response({
            'status': 'success',
            'payment_id': payment.id,
            'message': 'Payment verified successfully'
        }, status=200)


class PaymentWebhookView(APIView):
    """Handle Razorpay webhooks"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Verify webhook signature
        # signature = request.headers.get('X-Razorpay-Signature')
        # Implement signature verification
        
        event = request.data.get('event')
        payload = request.data.get('payload', {})
        
        if event == 'payment.captured':
            payment_entity = payload.get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            
            try:
                payment = Payment.objects.get(razorpay_order_id=order_id)
                payment.status = 'CAPTURED'
                payment.captured_at = timezone.now()
                payment.payment_method = payment_entity.get('method')
                payment.save()
            except Payment.DoesNotExist:
                pass
        
        elif event == 'payment.failed':
            payment_entity = payload.get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            
            try:
                payment = Payment.objects.get(razorpay_order_id=order_id)
                payment.status = 'FAILED'
                payment.error_code = payment_entity.get('error_code')
                payment.error_description = payment_entity.get('error_description')
                payment.save()
            except Payment.DoesNotExist:
                pass
        
        return Response({'status': 'received'}, status=200)


class RequestRefundView(APIView):
    """Student requests refund"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def post(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id, student=request.user)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=404)
        
        if payment.status != 'CAPTURED':
            return Response({'error': 'Payment not eligible for refund'}, status=400)
        
        reason = request.data.get('reason')
        description = request.data.get('description', '')
        refund_amount = request.data.get('refund_amount', payment.amount)
        
        # Create refund request
        refund = Refund.objects.create(
            payment=payment,
            student=request.user,
            refund_amount=refund_amount,
            reason=reason,
            description=description,
            status='REQUESTED'
        )
        
        return Response(
            RefundSerializer(refund).data,
            status=201
        )


class ProcessRefundView(APIView):
    """Admin processes refund request"""
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def post(self, request, refund_id):
        try:
            refund = Refund.objects.get(id=refund_id)
        except Refund.DoesNotExist:
            return Response({'error': 'Refund not found'}, status=404)
        
        action = request.data.get('action')  # 'approve' or 'reject'
        admin_notes = request.data.get('admin_notes', '')
        
        if action == 'approve':
            # Process refund
            razorpay_service = RazorpayService()
            
            try:
                razorpay_refund = razorpay_service.create_refund(
                    payment_id=refund.payment.razorpay_payment_id,
                    amount=float(refund.refund_amount),
                    notes={'refund_id': refund.id}
                )
                
                refund.razorpay_refund_id = razorpay_refund['id']
                refund.status = 'COMPLETED'
                refund.completed_at = timezone.now()
                
                # Update payment
                if float(refund.refund_amount) == float(refund.payment.amount):
                    refund.payment.status = 'REFUNDED'
                else:
                    refund.payment.status = 'PARTIALLY_REFUNDED'
                refund.payment.save()
                
            except Exception as e:
                refund.status = 'FAILED'
                refund.admin_notes = f"Refund failed: {str(e)}"
                refund.save()
                return Response({'error': str(e)}, status=500)
        
        elif action == 'reject':
            refund.status = 'REJECTED'
        
        refund.reviewed_by = request.user
        refund.reviewed_at = timezone.now()
        refund.admin_notes = admin_notes
        refund.save()
        
        return Response(RefundSerializer(refund).data, status=200)


class TeacherEarningsView(APIView):
    """Teacher views earnings and payouts"""
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    def get(self, request):
        # Total earnings
        total_captured = Payment.objects.filter(
            session__teacher=request.user,
            status='CAPTURED'
        ).aggregate(total=Sum('teacher_amount'))['total'] or 0
        
        # In escrow
        in_escrow = Payment.objects.filter(
            session__teacher=request.user,
            status='CAPTURED',
            is_held_in_escrow=True,
            released_from_escrow=False
        ).aggregate(total=Sum('teacher_amount'))['total'] or 0
        
        # Paid out
        paid_out = Payout.objects.filter(
            teacher=request.user,
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Pending payouts
        pending_payouts = Payout.objects.filter(
            teacher=request.user,
            status__in=['PENDING', 'PROCESSING']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'total_earnings': float(total_captured),
            'in_escrow': float(in_escrow),
            'available_for_payout': float(total_captured - in_escrow - paid_out - pending_payouts),
            'paid_out': float(paid_out),
            'pending_payouts': float(pending_payouts)
        })


class AddBankAccountView(APIView):
    """Teacher adds bank account for payouts"""
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def post(self, request):
        serializer = TeacherBankAccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(teacher=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class DownloadInvoiceView(APIView):
    """Download invoice PDF"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, invoice_id):
        try:
            invoice = Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=404)
        
        # Check permissions
        if request.user.id != invoice.payment.student_id:
            if not request.user.is_staff:
                return Response({'error': 'Permission denied'}, status=403)
        
        if invoice.pdf_file:
            response = HttpResponse(invoice.pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
            return response
        
        return Response({'error': 'PDF not generated'}, status=404)
