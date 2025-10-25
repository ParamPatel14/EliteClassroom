'use client';

import { useState, useEffect } from 'react';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface Resource {
  id: number;
  title: string;
  description: string;
  resource_type: string;
  file: string;
  external_link: string;
  course_title: string;
  category: string;
}

export default function ResourcesPage() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchResources = async () => {
    setLoading(true);
    try {
      const params = search ? `?search=${search}` : '';
      const response = await axiosInstance.get(`/courses/resources/${params}`);
      setResources(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching resources:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
  }, []);

  const handleSearch = () => {
    fetchResources();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Free Learning Resources</h1>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex gap-4">
            <Input
              placeholder="Search resources..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
            />
            <Button onClick={handleSearch} variant="primary">
              Search
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {resources.map((resource) => (
              <div key={resource.id} className="bg-white rounded-lg shadow-md p-6">
                <div className="mb-2">
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                    {resource.resource_type}
                  </span>
                </div>
                <h3 className="text-lg font-semibold mb-2">{resource.title}</h3>
                <p className="text-sm text-gray-600 mb-4">
                  {resource.description.substring(0, 100)}...
                </p>
                {resource.course_title && (
                  <p className="text-xs text-gray-500 mb-4">
                    Course: {resource.course_title}
                  </p>
                )}
                <Button
                  variant="primary"
                  className="w-full"
                  onClick={() => {
                    if (resource.external_link) {
                      window.open(resource.external_link, '_blank');
                    }
                  }}
                >
                  Access Resource
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
