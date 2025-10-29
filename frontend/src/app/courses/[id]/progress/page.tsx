'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';

interface Module {
  id: number;
  title: string;
  description: string;
  order: number;
  estimated_hours: number;
}

interface Progress {
  id: number;
  module: Module;
  is_completed: boolean;
  completion_percentage: number;
  time_spent_minutes: number;
}

export default function CourseProgressPage() {
  const params = useParams();
  const [enrollmentId, setEnrollmentId] = useState<number | null>(null);
  const [progress, setProgress] = useState<Progress[]>([]);

  useEffect(() => {
    const load = async () => {
      // First get enrollment ID for this course
      const enrollRes = await axiosInstance.get('/courses/student/dashboard/');
      const enroll = enrollRes.data.enrollments.find((e: any) => e.course.id === Number(params.id));
      if (enroll) {
        setEnrollmentId(enroll.id);
        const progRes = await axiosInstance.get(`/courses/enrollments/${enroll.id}/progress/`);
        setProgress(progRes.data.results || progRes.data);
      }
    };
    load();
  }, [params]);

  const updateProgress = async (progressId: number, percentage: number) => {
    await axiosInstance.patch(`/courses/progress/${progressId}/update/`, {
      completion_percentage: percentage
    });
    // Reload
    if (enrollmentId) {
      const progRes = await axiosInstance.get(`/courses/enrollments/${enrollmentId}/progress/`);
      setProgress(progRes.data.results || progRes.data);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Course Progress</h1>

      <div className="space-y-4">
        {progress.map(p => (
          <div key={p.id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-lg font-semibold">Module {p.module.order}: {p.module.title}</h3>
                <p className="text-sm text-gray-600">{p.module.description}</p>
                <p className="text-xs text-gray-500 mt-1">Est. {p.module.estimated_hours}h • Spent: {Math.round(p.time_spent_minutes/60)}h</p>
              </div>
              {p.is_completed && <span className="text-green-600 font-semibold">✓ Completed</span>}
            </div>

            <div className="mb-3">
              <div className="bg-gray-200 rounded-full h-3">
                <div className="bg-blue-600 h-3 rounded-full" style={{width: `${p.completion_percentage}%`}}></div>
              </div>
              <p className="text-sm text-gray-600 mt-1">{p.completion_percentage}%</p>
            </div>

            {!p.is_completed && (
              <div className="flex gap-2">
                <Button onClick={()=>updateProgress(p.id, Math.min(p.completion_percentage + 25, 100))}>
                  +25%
                </Button>
                <Button onClick={()=>updateProgress(p.id, 100)}>
                  Mark Complete
                </Button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
