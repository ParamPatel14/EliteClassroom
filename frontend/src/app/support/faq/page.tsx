'use client';

import { useEffect, useState } from 'react';
import axiosInstance from '@/lib/axios';

interface FAQ {
  id: number;
  category: string;
  question: string;
  answer: string;
  helpful_count: number;
}

const categories = {
  ACCOUNT: 'Account & Login',
  BOOKING: 'Booking & Sessions',
  PAYMENT: 'Payment & Billing',
  TECHNICAL: 'Technical Issues',
  COURSES: 'Courses & Content',
  GENERAL: 'General Information'
};

export default function FAQPage() {
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    loadFAQs();
  }, [selectedCategory]);

  const loadFAQs = async () => {
    const params = selectedCategory ? `?category=${selectedCategory}` : '';
    const res = await axiosInstance.get(`/courses/faqs/${params}`);
    setFaqs(res.data.results || res.data);
  };

  const markHelpful = async (faqId: number, helpful: boolean) => {
    await axiosInstance.post(`/courses/faqs/${faqId}/feedback/`, { helpful });
    loadFAQs();
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Frequently Asked Questions</h1>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setSelectedCategory('')}
          className={`px-4 py-2 rounded-lg ${
            !selectedCategory ? 'bg-blue-600 text-white' : 'bg-gray-200'
          }`}
        >
          All
        </button>
        {Object.entries(categories).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setSelectedCategory(key)}
            className={`px-4 py-2 rounded-lg ${
              selectedCategory === key ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* FAQ List */}
      <div className="space-y-3">
        {faqs.map(faq => (
          <div key={faq.id} className="bg-white rounded-lg shadow-md">
            <button
              onClick={() => setExpandedId(expandedId === faq.id ? null : faq.id)}
              className="w-full text-left p-4 flex items-center justify-between hover:bg-gray-50"
            >
              <div className="flex-1">
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded mr-2">
                  {categories[faq.category as keyof typeof categories]}
                </span>
                <h3 className="font-semibold mt-2">{faq.question}</h3>
              </div>
              <span className="text-2xl">{expandedId === faq.id ? '−' : '+'}</span>
            </button>

            {expandedId === faq.id && (
              <div className="px-4 pb-4">
                <p className="text-gray-700 whitespace-pre-wrap mb-4">{faq.answer}</p>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-gray-500">Was this helpful?</span>
                  <button
                    onClick={() => markHelpful(faq.id, true)}
                    className="text-green-600 hover:underline"
                  >
                    👍 Yes ({faq.helpful_count})
                  </button>
                  <button
                    onClick={() => markHelpful(faq.id, false)}
                    className="text-red-600 hover:underline"
                  >
                    👎 No
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
