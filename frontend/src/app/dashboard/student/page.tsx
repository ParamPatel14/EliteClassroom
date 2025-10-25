'use client';

import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/Button';
import axiosInstance from '@/lib/axios';
import Link from 'next/link';

interface DashboardData {
  enrollments: any[];
  upcoming_sessions: any[];
  stats: {
    total_courses: number;
    completed_courses: number;
    total_sessions: number;
  };
}

export default function StudentDashboard() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (user?.role !== 'STUDENT') {
      router.push('/dashboard/teacher');
    } else {
      fetchDashboard();
    }
  }, [isAuthenticated, user, router]);

  const fetchDashboard = async () => {
    try {
      const response = await axiosInstance.get('/courses/student/dashboard/');
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!user || loading) return <div>Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Student Dashboard</h1>
          <div className="flex gap-4">
            <Link href="/teachers">
              <Button variant="outline">Find Teachers</Button>
            </Link>
            <Link href="/resources">
              <Button variant="outline">Resources</Button>
            </Link>
            <Button onClick={handleLogout} variant="outline">
              Logout
            </Button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-2">Welcome back, {user.full_name}!</h2>
          <p className="text-gray-600">{user.email}</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Total Courses</h3>
            <p className="text-3xl font-bold text-blue-600">
              {dashboardData?.stats.total_courses || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Completed</h3>
            <p className="text-3xl font-bold text-green-600">
              {dashboardData?.stats.completed_courses || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Total Sessions</h3>
            <p className="text-3xl font-bold text-purple-600">
              {dashboardData?.stats.total_sessions || 0}
            </p>
          </div>
        </div>

        {/* Upcoming Sessions */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-xl font-semibold mb-4">Upcoming Sessions</h3>
          {dashboardData?.upcoming_sessions.length ? (
            <div className="space-y-4">
              {dashboardData.upcoming_sessions.map((session: any) => (
                <div key={session.id} className="border-l-4 border-blue-500 pl-4 py-2">
                  <h4 className="font-semibold">{session.title}</h4>
                  <p className="text-sm text-gray-600">
                    with {session.teacher.full_name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {new Date(session.scheduled_date).toLocaleDateString()} at {session.start_time}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600">No upcoming sessions</p>
          )}
        </div>

        {/* My Courses */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">My Courses</h3>
          {dashboardData?.enrollments.length ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dashboardData.enrollments.map((enrollment: any) => (
                <div key={enrollment.id} className="border rounded-lg p-4">
                  <h4 className="font-semibold">{enrollment.course.title}</h4>
                  <p className="text-sm text-gray-600 mb-2">
                    by {enrollment.course.teacher.full_name}
                  </p>
                  <div className="mb-2">
                    <div className="bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${enrollment.progress}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {enrollment.progress}% complete
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600">Not enrolled in any courses yet</p>
          )}
        </div>
      </main>
    </div>
  );
}
