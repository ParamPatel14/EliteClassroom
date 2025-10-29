'use client';

import { useEffect, useState } from 'react';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface Demo {
  id: number;
  title: string;
  subject: string;
  status: string;
  average_rating: number;
  view_count: number;
  uploaded_at: string;
}

export default function TeacherDemosPage() {
  const [demos, setDemos] = useState<Demo[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [thumbnail, setThumbnail] = useState<File | null>(null);
  const [form, setForm] = useState({
    title: '',
    description: '',
    subject: '',
    duration_minutes: '10',
    course: ''
  });
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const loadDemos = async () => {
    const res = await axiosInstance.get('/courses/teacher/demos/');
    setDemos(res.data.results || res.data);
  };

  useEffect(() => { loadDemos(); }, []);

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a video file');
      return;
    }
    
    setUploading(true);
    setUploadProgress(0);

    try {
      const fd = new FormData();
      fd.append('original_video', file);
      if (thumbnail) fd.append('thumbnail', thumbnail);
      Object.entries(form).forEach(([k, v]) => v && fd.append(k, v));

      await axiosInstance.post('/courses/teacher/demos/upload/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) {
            setUploadProgress(Math.round((e.loaded * 100) / e.total));
          }
        }
      });

      await loadDemos();
      setForm({ title: '', description: '', subject: '', duration_minutes: '10', course: '' });
      setFile(null);
      setThumbnail(null);
      alert('Demo uploaded! Awaiting admin approval.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const statusColor = (status: string) => {
    if (status === 'APPROVED') return 'bg-green-100 text-green-700';
    if (status === 'REJECTED') return 'bg-red-100 text-red-700';
    return 'bg-yellow-100 text-yellow-700';
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Demo Lectures</h2>

      {/* Upload Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-xl font-semibold mb-4">Upload Demo</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <Input label="Title" value={form.title} onChange={(e)=>setForm({...form, title:e.target.value})} required />
          <Input label="Subject" value={form.subject} onChange={(e)=>setForm({...form, subject:e.target.value})} required />
          <Input label="Duration (minutes)" type="number" value={form.duration_minutes} onChange={(e)=>setForm({...form, duration_minutes:e.target.value})} />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea className="w-full border rounded p-2 min-h-[100px]" value={form.description} onChange={(e)=>setForm({...form, description:e.target.value})} />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">Video File (max 500MB)</label>
          <input type="file" accept="video/*" onChange={(e)=>setFile(e.target.files?.[0]||null)} />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">Thumbnail (optional)</label>
          <input type="file" accept="image/*" onChange={(e)=>setThumbnail(e.target.files?.[0]||null)} />
        </div>

        {uploading && (
          <div className="mb-4">
            <div className="bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{width: `${uploadProgress}%`}}></div>
            </div>
            <p className="text-sm text-gray-600 mt-1">Uploading: {uploadProgress}%</p>
          </div>
        )}

        <Button onClick={handleUpload} isLoading={uploading}>Upload Demo</Button>
      </div>

      {/* Demo List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">Your Demos</h3>
        <div className="space-y-3">
          {demos.map(d => (
            <div key={d.id} className="border rounded p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-semibold">{d.title}</h4>
                  <p className="text-sm text-gray-600">{d.subject}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Views: {d.view_count} • Rating: {d.average_rating.toFixed(1)}⭐
                  </p>
                </div>
                <span className={`px-2 py-1 text-xs rounded ${statusColor(d.status)}`}>
                  {d.status}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-2">Uploaded: {new Date(d.uploaded_at).toLocaleDateString()}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
