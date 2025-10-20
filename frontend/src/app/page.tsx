'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.role === 'STUDENT') {
        router.push('/dashboard/student');
      } else if (user.role === 'TEACHER') {
        router.push('/dashboard/teacher');
      }
    }
  }, [isAuthenticated, user, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Elite Classroom
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Connect with expert teachers and elevate your learning experience
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/register">
              <Button variant="primary" className="px-8 py-3 text-lg">
                Get Started
              </Button>
            </Link>
            <Link href="/login">
              <Button variant="outline" className="px-8 py-3 text-lg">
                Sign In
              </Button>
            </Link>
          </div>
        </div>

        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold mb-3">Expert Teachers</h3>
            <p className="text-gray-600">
              Learn from verified, experienced teachers across various subjects
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold mb-3">AI-Powered Learning</h3>
            <p className="text-gray-600">
              Personalized learning experience with AI assistance and voice chat
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold mb-3">Flexible Sessions</h3>
            <p className="text-gray-600">
              Choose between online and offline classes based on your convenience
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
