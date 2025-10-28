'use client';

import { useEffect, useState } from 'react';
import axiosInstance from '@/lib/axios';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/store/authStore';

export default function TeacherProfileBuilderPage() {
  const { user } = useAuthStore();
  const u = user as any;
  const [form, setForm] = useState({
    first_name: u?.first_name || '',
    last_name: u?.last_name || '',
    bio: u?.bio || '',
    city: u?.city || '',
    state: u?.state || '',
    country: u?.country || '',
  });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const handleChange = (e: any) => setForm({ ...form, [e.target.name]: e.target.value });

  const save = async () => {
    setSaving(true);
    setMsg('');
    try {
      await axiosInstance.patch('/courses/teacher/profile/', form);
      setMsg('Profile updated');
    } catch (e: any) {
      setMsg('Failed to update');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Teacher Profile</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input label="First name" name="first_name" value={form.first_name} onChange={handleChange}/>
        <Input label="Last name" name="last_name" value={form.last_name} onChange={handleChange}/>
        <Input label="City" name="city" value={form.city} onChange={handleChange}/>
        <Input label="State" name="state" value={form.state} onChange={handleChange}/>
        <Input label="Country" name="country" value={form.country} onChange={handleChange}/>
      </div>
      <div className="mt-4">
        <label className="block text-sm font-medium mb-1">Bio</label>
        <textarea name="bio" value={form.bio} onChange={handleChange}
          className="w-full border rounded p-2 min-h-[120px]" />
      </div>
      <div className="mt-4 flex gap-2">
        <Button onClick={save} isLoading={saving}>Save</Button>
        {msg && <span className="text-sm text-gray-600">{msg}</span>}
      </div>
    </div>
  );
}
