'use client';

import { useState } from 'react';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function BankAccountPage() {
  const [form, setForm] = useState({
    account_holder_name: '',
    account_number: '',
    ifsc_code: '',
    bank_name: '',
    branch_name: ''
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await axiosInstance.post('/courses/teacher/bank-account/', form);
      alert('Bank account added! Awaiting verification.');
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to add account');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Add Bank Account</h1>

      <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
        <Input
          label="Account Holder Name"
          value={form.account_holder_name}
          onChange={(e) => setForm({ ...form, account_holder_name: e.target.value })}
          required
        />
        <Input
          label="Account Number"
          value={form.account_number}
          onChange={(e) => setForm({ ...form, account_number: e.target.value })}
          required
        />
        <Input
          label="IFSC Code"
          value={form.ifsc_code}
          onChange={(e) => setForm({ ...form, ifsc_code: e.target.value })}
          required
        />
        <Input
          label="Bank Name"
          value={form.bank_name}
          onChange={(e) => setForm({ ...form, bank_name: e.target.value })}
          required
        />
        <Input
          label="Branch Name"
          value={form.branch_name}
          onChange={(e) => setForm({ ...form, branch_name: e.target.value })}
        />

        <Button onClick={handleSubmit} isLoading={submitting} className="w-full mt-4">
          Submit for Verification
        </Button>
      </div>
    </div>
  );
}
