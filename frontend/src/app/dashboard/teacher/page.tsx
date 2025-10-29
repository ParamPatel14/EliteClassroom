'use client';

import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';

export default function TeacherDashboard() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (user?.role !== 'TEACHER') {
      router.push('/dashboard/student');
    }
  }, [isAuthenticated, user, router]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Teacher Dashboard</h1>
          <Button onClick={handleLogout} variant="outline">
            Logout
          </Button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Welcome, {user.full_name}!</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-gray-600">Email:</p>
              <p className="font-medium">{user.email}</p>
            </div>
            <div>
              <p className="text-gray-600">Role:</p>
              <p className="font-medium">{user.role}</p>
            </div>
            {user.teacher_profile && (
              <>
                <div>
                  <p className="text-gray-600">Experience:</p>
                  <p className="font-medium">
                    {user.teacher_profile.years_of_experience} years
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Total Sessions:</p>
                  <p className="font-medium">{user.teacher_profile.total_sessions}</p>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Today's Sessions</h3>
            <p className="text-gray-600">No sessions scheduled</p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">My Students</h3>
            <p className="text-gray-600">0 students</p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Earnings</h3>
            <p className="text-gray-600">₹0</p>
          </div>
          <Link href="/dashboard/teacher/demos"><Button>Demo Lectures</Button></Link>
        </div>
      </main>
    </div>
  );
}
