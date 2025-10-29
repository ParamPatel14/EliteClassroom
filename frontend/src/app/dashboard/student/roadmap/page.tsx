'use client';

import { useEffect, useState } from 'react';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface Roadmap {
  id: number;
  title: string;
  description: string;
  goal: string;
  progress_percentage: number;
  is_active: boolean;
  courses: any[];
}

export default function LearningRoadmapPage() {
  const [roadmaps, setRoadmaps] = useState<Roadmap[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    title: '',
    description: '',
    goal: '',
    target_completion_date: '',
    estimated_hours_per_week: '5',
    course_ids: ''
  });

  const load = async () => {
    const res = await axiosInstance.get('/courses/student/roadmaps/');
    setRoadmaps(res.data.results || res.data);
  };

  useEffect(() => { load(); }, []);

  const createRoadmap = async () => {
    try {
      const courseIds = form.course_ids.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
      await axiosInstance.post('/courses/student/roadmaps/', {
        ...form,
        course_ids: courseIds
      });
      await load();
      setShowCreate(false);
      setForm({ title: '', description: '', goal: '', target_completion_date: '', estimated_hours_per_week: '5', course_ids: '' });
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create roadmap');
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">My Learning Roadmaps</h1>
        <Button onClick={()=>setShowCreate(!showCreate)}>
          {showCreate ? 'Cancel' : 'Create Roadmap'}
        </Button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-xl font-semibold mb-4">Create New Roadmap</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <Input label="Title" value={form.title} onChange={(e)=>setForm({...form, title:e.target.value})} />
            <Input label="Target Date" type="date" value={form.target_completion_date} onChange={(e)=>setForm({...form, target_completion_date:e.target.value})} />
            <Input label="Hours/Week" type="number" value={form.estimated_hours_per_week} onChange={(e)=>setForm({...form, estimated_hours_per_week:e.target.value})} />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Goal</label>
            <textarea className="w-full border rounded p-2" value={form.goal} onChange={(e)=>setForm({...form, goal:e.target.value})} />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Course IDs (comma-separated)</label>
            <Input placeholder="e.g., 1,2,3" value={form.course_ids} onChange={(e)=>setForm({...form, course_ids:e.target.value})} />
          </div>
          <Button onClick={createRoadmap}>Create</Button>
        </div>
      )}

      <div className="space-y-4">
        {roadmaps.map(rm => (
          <div key={rm.id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-xl font-semibold">{rm.title}</h3>
                <p className="text-sm text-gray-600 mt-1">{rm.description}</p>
                <p className="text-sm text-gray-500 mt-1">Goal: {rm.goal}</p>
              </div>
              <span className={`px-2 py-1 text-xs rounded ${rm.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                {rm.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>

            <div className="mb-3">
              <div className="bg-gray-200 rounded-full h-3">
                <div className="bg-purple-600 h-3 rounded-full" style={{width: `${rm.progress_percentage}%`}}></div>
              </div>
              <p className="text-sm text-gray-600 mt-1">{rm.progress_percentage}% complete</p>
            </div>

            <div>
              <p className="text-sm font-medium mb-2">Courses ({rm.courses.length}):</p>
              <div className="flex flex-wrap gap-2">
                {rm.courses.map((c: any) => (
                  <span key={c.id} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                    {c.course.title} {c.is_completed && '✓'}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
