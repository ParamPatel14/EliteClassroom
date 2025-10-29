'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import axiosInstance from '@/lib/axios';

export default function ChatPage() {
  const params = useParams();
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [text, setText] = useState('');
  const [msgs, setMsgs] = useState<{sender:string; text:string; at:string}[]>([]);

  useEffect(() => {
    const sock = new WebSocket(`ws://127.0.0.1:8000/ws/chat/${params.id}/`);
    sock.onmessage = (evt) => {
      try {
        const m = JSON.parse(evt.data);
        setMsgs(prev => [...prev, m]);
      } catch {}
    };
    setWs(sock);
    return () => { sock.close(); };
  }, [params]);

  const send = () => {
    if (!text.trim() || !ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ text, at: new Date().toISOString() }));
    setText('');
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="border rounded h-96 overflow-y-auto p-3 mb-3 bg-white">
        {msgs.map((m, i)=>(
          <div key={i} className="mb-2">
            <div className="text-xs text-gray-500">{m.at}</div>
            <div>{m.text}</div>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="border rounded px-3 py-2 flex-1" value={text} onChange={e=>setText(e.target.value)} placeholder="Type a message"/>
        <button className="px-3 py-2 bg-blue-600 text-white rounded" onClick={send}>Send</button>
      </div>
    </div>
  );
}
