'use client';

import { useEffect, useState } from 'react';
import axiosInstance from '@/lib/axios';

interface Analytics {
  completion_rate: number;
  average_test_score: number;
  total_sessions: number;
  learning_pace: string;
  strengths: string[];
  weaknesses: string[];
  at_risk_of_dropout: boolean;
}

export default function ProgressWidget() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);

  useEffect(() => {
    const load = async () => {
      const res = await axiosInstance.get('/courses/student/analytics/');
      setAnalytics(res.data);
    };
    load();
  }, []);

  if (!analytics) return null;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-semibold mb-4">Your Progress</h3>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-600">Completion Rate</p>
          <p className="text-2xl font-bold text-blue-600">{analytics.completion_rate}%</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Avg Test Score</p>
          <p className="text-2xl font-bold text-green-600">{analytics.average_test_score}%</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Total Sessions</p>
          <p className="text-2xl font-bold">{analytics.total_sessions}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Learning Pace</p>
          <p className="text-lg font-medium">{analytics.learning_pace}</p>
        </div>
      </div>

      {analytics.at_risk_of_dropout && (
        <div className="bg-red-50 border border-red-200 rounded p-3 mb-4">
          <p className="text-sm text-red-700">⚠️ You might benefit from more frequent sessions</p>
        </div>
      )}

      <div className="mb-3">
        <p className="text-sm font-medium mb-1">Strengths:</p>
        <div className="flex flex-wrap gap-2">
          {analytics.strengths.map((s, i) => (
            <span key={i} className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">{s}</span>
          ))}
        </div>
      </div>

      <div>
        <p className="text-sm font-medium mb-1">Focus Areas:</p>
        <div className="flex flex-wrap gap-2">
          {analytics.weaknesses.map((w, i) => (
            <span key={i} className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded">{w}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
