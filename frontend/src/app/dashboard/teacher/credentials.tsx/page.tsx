'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface Cred {
  id: number;
  degree?: string;
  institution?: string;
  year?: number;
  certification_name?: string;
  achievement?: string;
  document?: string;
  verified: boolean;
  submitted_at: string;
  verified_at?: string;
}

export default function CredentialsPage() {
  const [list, setList] = useState<Cred[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState({ degree: '', institution: '', year: '', certification_name: '', achievement: '' });
  const [loading, setLoading] = useState(false);

  const load = async () => {
    const res = await axiosInstance.get('/courses/teacher/credentials/');
    setList(res.data.results || res.data);
  };

  useEffect(() => { load(); }, []);

  const submit = async () => {
    setLoading(true);
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => v && fd.append(k, String(v)));
      if (file) fd.append('document', file);
      await axiosInstance.post('/courses/teacher/credentials/', fd, { headers: { 'Content-Type': 'multipart/form-data' }});
      await load();
      setForm({ degree: '', institution: '', year: '', certification_name: '', achievement: '' });
      setFile(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Credentials</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <Input label="Degree" name="degree" value={form.degree} onChange={(e)=>setForm({...form, degree:e.target.value})}/>
        <Input label="Institution" name="institution" value={form.institution} onChange={(e)=>setForm({...form, institution:e.target.value})}/>
        <Input label="Year" name="year" type="number" value={form.year} onChange={(e)=>setForm({...form, year:e.target.value})}/>
        <Input label="Certification Name" name="certification_name" value={form.certification_name} onChange={(e)=>setForm({...form, certification_name:e.target.value})}/>
      </div>
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Achievements</label>
        <textarea className="w-full border rounded p-2 min-h-[100px]" value={form.achievement} onChange={(e)=>setForm({...form, achievement:e.target.value})}/>
      </div>
      <div className="mb-4">
        <input type="file" onChange={(e)=>setFile(e.target.files?.[0] || null)} />
      </div>
      <Button onClick={submit} isLoading={loading}>Submit Credential</Button>

      <h3 className="text-xl font-semibold mt-8 mb-3">Submitted</h3>
      <div className="space-y-3">
        {list.map(c => (
          <div key={c.id} className="border rounded p-3">
            <div className="flex items-center justify-between">
              <p className="font-medium">{c.degree || c.certification_name} — {c.institution}</p>
              <span className={`px-2 py-1 text-xs rounded ${c.verified ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                {c.verified ? 'Verified' : 'Pending'}
              </span>
            </div>
            {c.achievement && <p className="text-sm text-gray-600 mt-1">{c.achievement}</p>}
            <p className="text-xs text-gray-500 mt-1">Submitted: {new Date(c.submitted_at).toLocaleString()}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
