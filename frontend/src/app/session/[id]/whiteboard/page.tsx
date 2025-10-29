'use client';

import dynamic from 'next/dynamic';
import { useEffect, useRef, useState } from 'react';
import { useParams } from 'next/navigation';

const Excalidraw = dynamic(() => import('@excalidraw/excalidraw').then(m => m.Excalidraw), { ssr: false });

export default function WhiteboardPage() {
  const params = useParams();
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [elements, setElements] = useState<readonly any[]>([]);
  const [appState, setAppState] = useState<any>({});
  const [scrollToContent, setScrollToContent] = useState(true);

  useEffect(() => {
    const sock = new WebSocket(`ws://127.0.0.1:8000/ws/whiteboard/${params.id}/`);
    sock.onmessage = (evt) => {
      try {
        const payload = JSON.parse(evt.data);
        if (payload.type === 'sync' && payload.elements) {
          setElements(payload.elements);
        }
        if (payload.type === 'draw_ops' && payload.elements) {
          setElements(payload.elements);
        }
        if (payload.type === 'clear') {
          setElements([]);
        }
      } catch {}
    };
    setWs(sock);
    return () => { sock.close(); };
  }, [params]);

  return (
    <div className="h-screen">
      <Excalidraw
        initialData={{ elements }}
        onChange={(els, state) => {
          setElements(els);
          setAppState(state);
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'draw_ops', elements: els }));
          }
        }}
      />
      <div className="p-2">
        <button className="px-3 py-2 bg-gray-200 rounded" onClick={()=>{
          setElements([]);
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'clear' }));
          }
        }}>Clear</button>
      </div>
    </div>
  );
}
