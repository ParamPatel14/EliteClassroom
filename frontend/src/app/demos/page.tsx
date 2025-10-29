'use client';

import { useEffect, useState } from 'react';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import Link from 'next/link';

interface Demo {
  id: number;
  title: string;
  teacher_name: string;
  subject: string;
  duration_minutes: number;
  thumbnail: string;
  average_rating: number;
  total_ratings: number;
  view_count: number;
}

export default function DemoBrowsePage() {
  const [demos, setDemos] = useState<Demo[]>([]);
  const [search, setSearch] = useState('');
  const [subject, setSubject] = useState('');
  const [loading, setLoading] = useState(false);

  const loadDemos = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (subject) params.append('subject', subject);
      const res = await axiosInstance.get(`/courses/demos/?${params}`);
      setDemos(res.data.results || res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadDemos(); }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">Demo Lectures</h1>

        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input placeholder="Search demos..." value={search} onChange={(e)=>setSearch(e.target.value)} />
            <Input placeholder="Subject filter" value={subject} onChange={(e)=>setSubject(e.target.value)} />
            <Button onClick={loadDemos} isLoading={loading}>Search</Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {demos.map(d => (
            <Link key={d.id} href={`/demos/${d.id}`} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition">
              <div className="aspect-video bg-gray-200 relative">
                {d.thumbnail ? (
                  <img src={d.thumbnail} alt={d.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-400">No thumbnail</div>
                )}
                <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                  {d.duration_minutes} min
                </div>
              </div>
              <div className="p-4">
                <h3 className="font-semibold mb-1">{d.title}</h3>
                <p className="text-sm text-gray-600 mb-2">by {d.teacher_name}</p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>{d.subject}</span>
                  <span>{d.average_rating.toFixed(1)}⭐ ({d.total_ratings})</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
