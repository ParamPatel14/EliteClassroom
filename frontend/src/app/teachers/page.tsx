'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface Teacher {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  city: string;
  teacher_profile: {
    years_of_experience: number;
    subjects_taught: string[];
    hourly_rate: number;
    average_rating: number;
    total_reviews: number;
  };
}

export default function TeacherSearchPage() {
  const { user } = useAuthStore();
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    search: '',
    subject: '',
    min_rating: '',
    max_rate: '',
    city: '',
    availability: '',
  });

  const fetchTeachers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await axiosInstance.get(
        `/courses/teachers/search/?${params.toString()}`
      );
      setTeachers(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching teachers:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeachers();
  }, []);

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value,
    });
  };

  const handleSearch = () => {
    fetchTeachers();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Find Your Perfect Teacher</h1>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              name="search"
              placeholder="Search by name..."
              value={filters.search}
              onChange={handleFilterChange}
            />
            <Input
              name="subject"
              placeholder="Subject (e.g., Math)"
              value={filters.subject}
              onChange={handleFilterChange}
            />
            <Input
              name="city"
              placeholder="City"
              value={filters.city}
              onChange={handleFilterChange}
            />
            <Input
              name="min_rating"
              type="number"
              placeholder="Min Rating (1-5)"
              value={filters.min_rating}
              onChange={handleFilterChange}
            />
            <Input
              name="max_rate"
              type="number"
              placeholder="Max Hourly Rate"
              value={filters.max_rate}
              onChange={handleFilterChange}
            />
            <select
              name="availability"
              value={filters.availability}
              onChange={handleFilterChange}
              className="px-4 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">All Availability</option>
              <option value="online">Online</option>
              <option value="offline">Offline</option>
            </select>
          </div>
          <Button onClick={handleSearch} className="mt-4" variant="primary">
            Search Teachers
          </Button>
        </div>

        {/* Results */}
        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {teachers.map((teacher) => (
              <div key={teacher.id} className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold mb-2">{teacher.full_name}</h3>
                <p className="text-gray-600 mb-2">{teacher.city || 'Location not specified'}</p>
                
                <div className="mb-4">
                  <p className="text-sm text-gray-500">
                    Experience: {teacher.teacher_profile.years_of_experience} years
                  </p>
                  <p className="text-sm text-gray-500">
                    Rate: ₹{teacher.teacher_profile.hourly_rate}/hour
                  </p>
                  <p className="text-sm text-gray-500">
                    Rating: {teacher.teacher_profile.average_rating.toFixed(1)} ⭐
                    ({teacher.teacher_profile.total_reviews} reviews)
                  </p>
                </div>

                <div className="mb-4">
                  <p className="text-sm font-medium mb-1">Subjects:</p>
                  <div className="flex flex-wrap gap-2">
                    {teacher.teacher_profile.subjects_taught.slice(0, 3).map((subject, idx) => (
                      <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                        {subject}
                      </span>
                    ))}
                  </div>
                </div>

                <Button variant="primary" className="w-full">
                  Book Session
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
