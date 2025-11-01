'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';

interface Question {
  id: number;
  order: number;
  question_text: string;
  question_type: string;
  options: string[];
}

export default function TakeTestPage() {
  const params = useParams();
  const router = useRouter();
  const [test, setTest] = useState<any>(null);
  const [attemptId, setAttemptId] = useState<number | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const load = async () => {
      const testRes = await axiosInstance.get(`/courses/tests/${params.id}/`);
      setTest(testRes.data);
      
      // Start attempt
      const attemptRes = await axiosInstance.post(`/courses/tests/${params.id}/start/`);
      setAttemptId(attemptRes.data.id);
    };
    load();
  }, [params]);

  const handleSubmit = async () => {
    if (!attemptId) return;
    
    const answersArray = Object.entries(answers).map(([qId, ans]) => ({
      question_id: parseInt(qId),
      selected_answer: ans
    }));

    setSubmitting(true);
    try {
      const res = await axiosInstance.post(
        `/courses/tests/attempts/${attemptId}/submit/`,
        { answers: answersArray }
      );
      
      alert(`Test submitted! Score: ${res.data.percentage}%`);
      router.push('/assessments');
    } catch (err) {
      alert('Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (!test) return <div className="p-6">Loading test...</div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-2">{test.title}</h1>
      <p className="text-gray-600 mb-6">{test.description}</p>

      <div className="space-y-6">
        {test.questions.map((q: Question) => (
          <div key={q.id} className="bg-white rounded-lg shadow-md p-6">
            <h3 className="font-semibold mb-3">
              {q.order + 1}. {q.question_text}
            </h3>
            
            {q.question_type === 'MCQ' && (
              <div className="space-y-2">
                {q.options.map((opt, idx) => (
                  <label key={idx} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name={`question_${q.id}`}
                      value={String.fromCharCode(65 + idx)}
                      onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                      className="w-4 h-4"
                    />
                    <span>{String.fromCharCode(65 + idx)}. {opt}</span>
                  </label>
                ))}
              </div>
            )}

            {q.question_type === 'SHORT_ANSWER' && (
              <textarea
                className="w-full border rounded p-2 min-h-[100px]"
                placeholder="Your answer..."
                value={answers[q.id] || ''}
                onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
              />
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 flex justify-end">
        <Button onClick={handleSubmit} isLoading={submitting}>
          Submit Test
        </Button>
      </div>
    </div>
  );
}
