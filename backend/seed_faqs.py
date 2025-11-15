import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from courses.models import SupportFAQ

faqs = [
    {
        'category': 'ACCOUNT',
        'question': 'How do I reset my password?',
        'answer': 'To reset your password:\n1. Click "Forgot Password" on the login page\n2. Enter your registered email\n3. Check your inbox for reset link\n4. Click the link and set a new password\n\nIf you don\'t receive the email, check your spam folder or contact support@eliteclassroom.com',
        'keywords': ['password', 'reset', 'forgot', 'login'],
        'order': 1
    },
    {
        'category': 'ACCOUNT',
        'question': 'How do I verify my email address?',
        'answer': 'After registering, check your email for a verification link. Click the link to activate your account. If you didn\'t receive it:\n1. Log in to your account\n2. Go to Settings\n3. Click "Resend Verification Email"',
        'keywords': ['email', 'verify', 'activation', 'register'],
        'order': 2
    },
    {
        'category': 'BOOKING',
        'question': 'How do I book a session with a teacher?',
        'answer': 'To book a session:\n1. Browse teachers using the "Find Teachers" page\n2. Click on a teacher profile\n3. Check their availability calendar\n4. Select a time slot\n5. Confirm booking and make payment\n\nYou\'ll receive confirmation via email.',
        'keywords': ['book', 'session', 'teacher', 'schedule'],
        'order': 1
    },
    {
        'category': 'BOOKING',
        'question': 'Can I cancel or reschedule a session?',
        'answer': 'Yes! You can cancel or reschedule up to 24 hours before the session:\n1. Go to "My Sessions"\n2. Find the session\n3. Click "Reschedule" or "Cancel"\n\nCancellations within 24 hours may not be refundable. Check our cancellation policy for details.',
        'keywords': ['cancel', 'reschedule', 'refund', 'policy'],
        'order': 2
    },
    {
        'category': 'PAYMENT',
        'question': 'What payment methods do you accept?',
        'answer': 'We accept:\n- Credit/Debit cards (Visa, Mastercard, Amex)\n- UPI payments\n- Net banking\n- Wallet payments (Paytm, PhonePe)\n\nAll payments are secured with 256-bit SSL encryption.',
        'keywords': ['payment', 'credit card', 'upi', 'methods'],
        'order': 1
    },
    {
        'category': 'PAYMENT',
        'question': 'How do refunds work?',
        'answer': 'Refund eligibility:\n- Full refund if cancelled 24+ hours before session\n- 50% refund if cancelled 12-24 hours before\n- No refund for cancellations < 12 hours\n\nRefunds are processed within 5-7 business days to your original payment method.',
        'keywords': ['refund', 'cancel', 'money back'],
        'order': 2
    },
    {
        'category': 'TECHNICAL',
        'question': 'Video session is not working. What should I do?',
        'answer': 'Try these steps:\n1. Check your internet connection\n2. Refresh the page\n3. Allow camera/microphone permissions in browser\n4. Use Chrome or Firefox (recommended)\n5. Clear browser cache\n\nStill having issues? Contact support with your session ID.',
        'keywords': ['video', 'camera', 'microphone', 'not working'],
        'order': 1
    },
    {
        'category': 'COURSES',
        'question': 'How do I enroll in a course?',
        'answer': 'To enroll:\n1. Browse courses on the "Courses" page\n2. Click on a course for details\n3. Click "Enroll Now"\n4. Complete payment\n\nYou\'ll get instant access to all course materials.',
        'keywords': ['enroll', 'course', 'join', 'access'],
        'order': 1
    },
    {
        'category': 'COURSES',
        'question': 'Can I get a certificate after completing a course?',
        'answer': 'Yes! You\'ll receive a digital certificate when you:\n1. Complete all modules (100%)\n2. Pass the final assessment (60%+)\n3. Submit course feedback\n\nCertificates are available in your Dashboard > Certificates.',
        'keywords': ['certificate', 'completion', 'finish'],
        'order': 2
    },
    {
        'category': 'GENERAL',
        'question': 'What is the AI Tutor feature?',
        'answer': 'Our AI Tutor provides 24/7 learning support:\n- Answer questions on any subject\n- Explain concepts step-by-step\n- Generate practice problems\n- Voice and text interaction\n\nAccess it from your dashboard or any course page.',
        'keywords': ['ai', 'tutor', 'chatbot', '24/7'],
        'order': 1
    },
]

def seed():
    print("Seeding FAQs...")
    for faq_data in faqs:
        faq, created = SupportFAQ.objects.get_or_create(
            question=faq_data['question'],
            defaults=faq_data
        )
        if created:
            print(f"✓ Created: {faq.question}")
        else:
            print(f"⚠ Exists: {faq.question}")
    
    print(f"\n✅ Seeded {len(faqs)} FAQs")

if __name__ == '__main__':
    seed()
