'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/store/authStore';

interface Demo {
  id: number;
  title: string;
  teacher_name: string;
  description: string;
  subject: string;
  transcoded_video: string;
  average_rating: number;
  total_ratings: number;
  view_count: number;
}

interface Rating {
  id: number;
  student_name: string;
  rating: number;
  review: string;
  created_at: string;
}

export default function DemoDetailPage() {
  const params = useParams();
  const { user } = useAuthStore();
  const [demo, setDemo] = useState<Demo | null>(null);
  const [ratings, setRatings] = useState<Rating[]>([]);
  const [myRating, setMyRating] = useState(5);
  const [myReview, setMyReview] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const load = async () => {
      const [demoRes, ratingsRes] = await Promise.all([
        axiosInstance.get(`/courses/demos/${params.id}/`),
        axiosInstance.get(`/courses/demos/${params.id}/ratings/`)
      ]);
      setDemo(demoRes.data);
      setRatings(ratingsRes.data.results || ratingsRes.data);
    };
    load();
  }, [params]);

  const submitRating = async () => {
    setSubmitting(true);
    try {
      await axiosInstance.post('/courses/demos/rate/', {
        demo: demo?.id,
        rating: myRating,
        review: myReview
      });
      alert('Rating submitted!');
      window.location.reload();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to submit rating');
    } finally {
      setSubmitting(false);
    }
  };

  if (!demo) return <div className="p-6">Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-2">{demo.title}</h1>
      <p className="text-gray-600 mb-4">by {demo.teacher_name} • {demo.subject}</p>

      <div className="bg-black rounded-lg overflow-hidden mb-6">
        {demo.transcoded_video ? (
          <video controls className="w-full">
            <source src={demo.transcoded_video} type="video/mp4" />
          </video>
        ) : (
          <div className="aspect-video flex items-center justify-center text-white">
            Video processing...
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <div>
            <span className="text-2xl font-bold">{demo.average_rating.toFixed(1)}</span>
            <span className="text-yellow-500 ml-1">⭐</span>
          </div>
          <div className="text-sm text-gray-600">
            {demo.total_ratings} ratings • {demo.view_count} views
          </div>
        </div>
        <p className="text-gray-700">{demo.description}</p>
      </div>

      {/* Rate Demo (Students only) */}
      {user?.role === 'STUDENT' && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-xl font-semibold mb-4">Rate This Demo</h3>
          <div className="flex items-center gap-2 mb-4">
            {[1,2,3,4,5].map(r => (
              <button key={r} onClick={()=>setMyRating(r)} className="text-3xl">
                {r <= myRating ? '⭐' : '☆'}
              </button>
            ))}
          </div>
          <textarea
            className="w-full border rounded p-2 mb-4 min-h-[100px]"
            placeholder="Write your review..."
            value={myReview}
            onChange={(e)=>setMyReview(e.target.value)}
          />
          <Button onClick={submitRating} isLoading={submitting}>Submit Rating</Button>
        </div>
      )}

      {/* Ratings List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">Reviews ({ratings.length})</h3>
        <div className="space-y-4">
          {ratings.map(r => (
            <div key={r.id} className="border-b pb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">{r.student_name}</span>
                <span className="text-sm text-gray-500">{new Date(r.created_at).toLocaleDateString()}</span>
              </div>
              <div className="text-yellow-500 mb-1">{'⭐'.repeat(r.rating)}</div>
              {r.review && <p className="text-gray-700">{r.review}</p>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
