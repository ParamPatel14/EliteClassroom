'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuthStore } from '@/store/authStore';

export default function CreateTicketPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [form, setForm] = useState({
    name: user?.full_name || '',
    email: user?.email || '',
    subject: '',
    description: '',
    category: 'GENERAL'
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const res = await axiosInstance.post('/courses/support/tickets/create/', form);
      alert(`Ticket created: ${res.data.ticket_number}`);
      router.push('/dashboard/student');
    } catch (err) {
      alert('Failed to create ticket');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Create Support Ticket</h1>

      <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
        <Input
          label="Your Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />

        <Input
          label="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />

        <div>
          <label className="block text-sm font-medium mb-1">Category</label>
          <select
            className="w-full border rounded-lg px-3 py-2"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          >
            <option value="ACCOUNT">Account & Login</option>
            <option value="BOOKING">Booking & Sessions</option>
            <option value="PAYMENT">Payment & Billing</option>
            <option value="TECHNICAL">Technical Issues</option>
            <option value="COURSES">Courses & Content</option>
            <option value="GENERAL">General</option>
          </select>
        </div>

        <Input
          label="Subject"
          value={form.subject}
          onChange={(e) => setForm({ ...form, subject: e.target.value })}
          required
        />

        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            className="w-full border rounded-lg px-3 py-2 min-h-[150px]"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Please describe your issue in detail..."
            required
          />
        </div>

        <Button onClick={handleSubmit} isLoading={submitting} className="w-full">
          Submit Ticket
        </Button>
      </div>
    </div>
  );
}
