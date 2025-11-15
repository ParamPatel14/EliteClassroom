'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';

interface MockTest {
  id: number;
  title: string;
  subject: string;
  difficulty: string;
  total_questions: number;
  duration_minutes: number;
  created_at: string;
}

interface Attempt {
  id: number;
  mock_test: { title: string };
  percentage: number;
  passed: boolean;
  started_at: string;
  scorecard_url: string;
}

export default function AssessmentsPage() {
  const [tests, setTests] = useState<MockTest[]>([]);
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const [testsRes, attemptsRes] = await Promise.all([
        axiosInstance.get('/courses/tests/'),
        axiosInstance.get('/courses/tests/attempts/')
      ]);
      setTests(testsRes.data.results || testsRes.data);
      setAttempts(attemptsRes.data.results || attemptsRes.data);
      setLoading(false);
    };
    load();
  }, []);

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">My Assessments</h1>

      {/* Available Tests */}
      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Available Tests</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {tests.map(test => (
            <div key={test.id} className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-2">{test.title}</h3>
              <p className="text-sm text-gray-600 mb-2">{test.subject}</p>
              <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                <span>{test.total_questions} questions</span>
                <span>{test.duration_minutes} min</span>
                <span className={`px-2 py-1 rounded text-xs ${
                  test.difficulty === 'EASY' ? 'bg-green-100 text-green-700' :
                  test.difficulty === 'HARD' ? 'bg-red-100 text-red-700' :
                  'bg-yellow-100 text-yellow-700'
                }`}>{test.difficulty}</span>
              </div>
              <Link href={`/assessments/${test.id}`}>
                <Button className="w-full">Start Test</Button>
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* Past Attempts */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Past Attempts</h2>
        <div className="space-y-3">
          {attempts.map(attempt => (
            <div key={attempt.id} className="bg-white rounded-lg shadow-md p-4 flex items-center justify-between">
              <div>
                <h4 className="font-medium">{attempt.mock_test.title}</h4>
                <p className="text-sm text-gray-600">
                  {new Date(attempt.started_at).toLocaleDateString()} • Score: {attempt.percentage}%
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-3 py-1 rounded text-sm font-medium ${
                  attempt.passed ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {attempt.passed ? 'Passed ✓' : 'Failed'}
                </span>
                {attempt.scorecard_url && (
                  <a href={attempt.scorecard_url} target="_blank" rel="noopener noreferrer">
                    <Button variant="outline" className="text-sm">Download PDF</Button>
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
