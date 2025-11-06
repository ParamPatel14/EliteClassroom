'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';

declare global {
  interface Window {
    Razorpay: any;
  }
}

export default function CheckoutPage() {
  const params = useParams();
  const router = useRouter();
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSession();
    loadRazorpayScript();
  }, [params]);

  const loadSession = async () => {
    const res = await axiosInstance.get(`/courses/sessions/${params.session_id}/`);
    setSession(res.data);
  };

  const loadRazorpayScript = () => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    document.body.appendChild(script);
  };

  const handlePayment = async () => {
    setLoading(true);

    try {
      // Create order
      const orderRes = await axiosInstance.post('/courses/payments/create-order/', {
        payment_type: 'SESSION',
        item_id: params.session_id
      });

      const { order_id, amount, currency, key_id, payment_id, platform_fee, teacher_amount } = orderRes.data;

      // Razorpay options
      const options = {
        key: key_id,
        amount: amount * 100, // Convert to paise
        currency: currency,
        name: 'Elite Classroom',
        description: `Session: ${session.title}`,
        order_id: order_id,
        handler: async (response: any) => {
          // Verify payment
          try {
            await axiosInstance.post('/courses/payments/verify/', {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature
            });

            alert('Payment successful! Session confirmed.');
            router.push('/dashboard/student');
          } catch (err) {
            alert('Payment verification failed');
          }
        },
        prefill: {
          name: session.student?.full_name || '',
          email: session.student?.email || '',
        },
        theme: {
          color: '#3b82f6'
        }
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  if (!session) return <div className="p-6">Loading...</div>;

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Checkout</h1>

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Session Details</h2>
        <div className="space-y-2">
          <p><span className="font-medium">Title:</span> {session.title}</p>
          <p><span className="font-medium">Teacher:</span> {session.teacher?.full_name}</p>
          <p><span className="font-medium">Date:</span> {session.scheduled_date}</p>
          <p><span className="font-medium">Duration:</span> {session.duration_minutes} minutes</p>
          <p className="text-2xl font-bold mt-4">₹{session.price}</p>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-blue-700">
          💡 Payment is held securely until session completion. Teacher receives payout after 24 hours.
        </p>
      </div>

      <Button onClick={handlePayment} isLoading={loading} className="w-full">
        Pay ₹{session.price}
      </Button>
    </div>
  );
}
