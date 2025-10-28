'use client';

import { useEffect, useState } from 'react';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';

const days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];

interface Avail { id:number; day_of_week:number; start_time:string; end_time:string; timezone:string; is_recurring:boolean; is_active:boolean; }

export default function AvailabilityPage() {
  const [tz, setTz] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC');
  const [list, setList] = useState<Avail[]>([]);
  const [form, setForm] = useState({ day_of_week: 0, start_time: '09:00', end_time: '11:00', timezone: tz, is_recurring: true });

  const load = async () => {
    const res = await axiosInstance.get('/courses/teacher/availability/');
    setList(res.data.results || res.data);
  };

  useEffect(() => { load(); }, []);

  const add = async () => {
    await axiosInstance.post('/courses/teacher/availability/', { ...form, timezone: tz });
    await load();
  };

  const remove = async (id:number) => {
    await axiosInstance.delete(`/courses/teacher/availability/${id}/`);
    await load();
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Availability</h2>

      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Timezone</label>
        <input className="border rounded px-3 py-2 w-full" value={tz} onChange={(e)=>setTz(e.target.value)} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end mb-4">
        <div>
          <label className="block text-sm font-medium mb-1">Day</label>
          <select className="border rounded px-3 py-2 w-full" value={form.day_of_week}
            onChange={e=>setForm({...form, day_of_week:Number(e.target.value)})}>
            {days.map((d, i)=>(<option key={i} value={i}>{d}</option>))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Start</label>
          <input className="border rounded px-3 py-2 w-full" type="time" value={form.start_time}
            onChange={e=>setForm({...form, start_time:e.target.value})}/>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">End</label>
          <input className="border rounded px-3 py-2 w-full" type="time" value={form.end_time}
            onChange={e=>setForm({...form, end_time:e.target.value})}/>
        </div>
        <Button onClick={add}>Add Slot</Button>
      </div>

      <div className="space-y-2">
        {list.map(av => (
          <div key={av.id} className="flex items-center justify-between border rounded p-3">
            <p>{days[av.day_of_week]} {av.start_time}–{av.end_time} ({av.timezone})</p>
            <Button variant="outline" onClick={()=>remove(av.id)}>Remove</Button>
          </div>
        ))}
      </div>
    </div>
  );
}
