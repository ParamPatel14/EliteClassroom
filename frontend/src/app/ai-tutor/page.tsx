'use client';

import { useEffect, useState, useRef } from 'react';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import VoiceChat from '@/components/ai/Voicechat';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  has_audio: boolean;
}

interface Conversation {
  id: number;
  title: string;
  message_count: number;
  started_at: string;
}

export default function AITutorPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showNewChat, setShowNewChat] = useState(false);
  const [newChatForm, setNewChatForm] = useState({
    title: '',
    subject: '',
    student_goal: ''
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadConversations = async () => {
    const res = await axiosInstance.get('/courses/ai/conversations/');
    setConversations(res.data.results || res.data);
    if ((res.data.results || res.data).length > 0) {
      selectConversation((res.data.results || res.data)[0].id);
    }
  };

  const selectConversation = async (id: number) => {
    setActiveConversation(id);
    const res = await axiosInstance.get(`/courses/ai/conversations/${id}/messages/`);
    const msgs = (res.data.results || res.data).filter((m: any) => m.role !== 'system');
    setMessages(msgs);
  };

  const createConversation = async () => {
    try {
      const res = await axiosInstance.post('/courses/ai/conversations/', newChatForm);
      await loadConversations();
      setShowNewChat(false);
      setNewChatForm({ title: '', subject: '', student_goal: '' });
      selectConversation(res.data.id);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create conversation');
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !activeConversation) return;

    const userMessage = input;
    setInput('');
    setLoading(true);

    // Optimistic UI update
    const tempMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
      has_audio: false
    };
    setMessages(prev => [...prev, tempMsg]);

    try {
      const res = await axiosInstance.post(
        `/courses/ai/conversations/${activeConversation}/chat/`,
        { message: userMessage }
      );

      // Replace temp message with real one and add assistant response
      setMessages(prev => [
        ...prev.filter(m => m.id !== tempMsg.id),
        res.data.user_message,
        res.data.assistant_message
      ]);

      // Update conversation list
      await loadConversations();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to send message');
      setMessages(prev => prev.filter(m => m.id !== tempMsg.id));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <Button onClick={() => setShowNewChat(true)} className="w-full">
            + New Chat
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {conversations.map(conv => (
            <div
              key={conv.id}
              onClick={() => selectConversation(conv.id)}
              className={`p-3 cursor-pointer hover:bg-gray-50 border-b ${
                activeConversation === conv.id ? 'bg-blue-50' : ''
              }`}
            >
              <p className="font-medium truncate">{conv.title || 'Untitled'}</p>
              <p className="text-xs text-gray-500">{conv.message_count} messages</p>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {showNewChat ? (
          <div className="p-6">
            <h2 className="text-2xl font-bold mb-4">Start New Conversation</h2>
            <div className="space-y-4 max-w-md">
                            {activeConversation && (
                <div className="border-t p-4 bg-gray-50">
                    <VoiceChat
                    conversationId={activeConversation}
                    onTranscript={(text) => {
                        // Add user message optimistically
                        setMessages(prev => [...prev, {
                        id: Date.now(),
                        role: 'user',
                        content: text,
                        created_at: new Date().toISOString(),
                        has_audio: true
                        }]);
                    }}
                    onResponse={(text) => {
                        // Add assistant response
                        setMessages(prev => [...prev, {
                        id: Date.now() + 1,
                        role: 'assistant',
                        content: text,
                        created_at: new Date().toISOString(),
                        has_audio: true
                        }]);
                        loadConversations(); // Refresh conversation list
                    }}
                    />


                    
                </div>
                )}
              <Input
                label="Title"
                value={newChatForm.title}
                onChange={(e) => setNewChatForm({ ...newChatForm, title: e.target.value })}
                placeholder="e.g., Calculus Help"
              />
              <Input
                label="Subject"
                value={newChatForm.subject}
                onChange={(e) => setNewChatForm({ ...newChatForm, subject: e.target.value })}
                placeholder="e.g., Mathematics"
              />
              <div>
                <label className="block text-sm font-medium mb-1">Learning Goal</label>
                <textarea
                  className="w-full border rounded p-2 min-h-[100px]"
                  value={newChatForm.student_goal}
                  onChange={(e) => setNewChatForm({ ...newChatForm, student_goal: e.target.value })}
                  placeholder="What do you want to learn?"
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={createConversation}>Start</Button>
                <Button variant="outline" onClick={() => setShowNewChat(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        ) : activeConversation ? (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map(msg => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-2xl px-4 py-3 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border shadow-sm'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    <p className="text-xs mt-2 opacity-70">
                      {new Date(msg.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t bg-white p-4">
              <div className="max-w-4xl mx-auto flex gap-2">
                <input
                  type="text"
                  className="flex-1 border rounded-lg px-4 py-2"
                  placeholder="Ask anything..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !loading && sendMessage()}
                  disabled={loading}
                />
                <Button onClick={sendMessage} isLoading={loading} disabled={loading}>
                  Send
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            Select a conversation or start a new one
          </div>
        )}
      </div>
    </div>
  );
}
