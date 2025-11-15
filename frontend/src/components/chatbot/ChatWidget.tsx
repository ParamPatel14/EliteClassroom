'use client';

import { useState, useEffect, useRef } from 'react';
import axiosInstance from '@/lib/axios';

interface Message {
  id: number;
  role: 'user' | 'bot';
  content: string;
  created_at: string;
}

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestedActions, setSuggestedActions] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && !sessionId) {
      initChat();
    }
  }, [isOpen]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initChat = async () => {
    try {
      const stored = localStorage.getItem('chatbot_session_id');
      const res = await axiosInstance.post('/courses/chatbot/init/', {
        session_id: stored,
        page_url: window.location.href
      });
      
      setSessionId(res.data.session_id);
      localStorage.setItem('chatbot_session_id', res.data.session_id);
      setMessages(res.data.messages);
    } catch (err) {
      console.error('Chat init failed:', err);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !sessionId) return;

    const userMsg = input;
    setInput('');
    setLoading(true);

    // Optimistic update
    const tempMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: userMsg,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempMsg]);

    try {
      const res = await axiosInstance.post('/courses/chatbot/message/', {
        session_id: sessionId,
        message: userMsg
      });

      setMessages(prev => [
        ...prev.filter(m => m.id !== tempMsg.id),
        tempMsg,
        res.data.message
      ]);

      setSuggestedActions(res.data.suggested_actions || []);
    } catch (err) {
      console.error('Send failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleActionClick = (action: string) => {
    if (action === 'Create Ticket' || action === 'Talk to human') {
      // Open ticket form
      window.open('/support/ticket', '_blank');
    } else {
      setInput(action);
    }
  };

  return (
    <>
      {/* Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 z-50 flex items-center justify-center"
      >
        {isOpen ? '✕' : '💬'}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-white rounded-lg shadow-2xl z-50 flex flex-col">
          {/* Header */}
          <div className="bg-blue-600 text-white p-4 rounded-t-lg">
            <h3 className="font-semibold">Support Assistant</h3>
            <p className="text-xs opacity-90">We typically reply instantly</p>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] px-4 py-2 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}

            {suggestedActions.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {suggestedActions.map((action, i) => (
                  <button
                    key={i}
                    onClick={() => handleActionClick(action)}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded-full text-xs"
                  >
                    {action}
                  </button>
                ))}
              </div>
            )}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-4 py-2 rounded-lg">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t p-4">
            <div className="flex gap-2">
              <input
                type="text"
                className="flex-1 border rounded-lg px-3 py-2 text-sm"
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
