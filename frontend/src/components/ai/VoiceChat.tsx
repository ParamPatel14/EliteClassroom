'use client';

import { useState, useRef, useEffect } from 'react';
import axiosInstance from '@/lib/axios';
import { Button } from '@/components/ui/Button';

interface VoiceChatProps {
  conversationId: number;
  onTranscript?: (text: string) => void;
  onResponse?: (text: string) => void;
}

export default function VoiceChat({ conversationId, onTranscript, onResponse }: VoiceChatProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processVoiceInput(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Failed to start recording:', err);
      alert('Microphone access denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processVoiceInput = async (audioBlob: Blob) => {
    setIsProcessing(true);

    try {
      // Convert blob to base64
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      
      reader.onloadend = async () => {
        const base64Audio = (reader.result as string).split(',')[1];

        const res = await axiosInstance.post(
          `/courses/ai/conversations/${conversationId}/voice/`,
          {
            audio: base64Audio,
            format: 'webm'
          }
        );

        // Show transcript
        if (onTranscript) {
          onTranscript(res.data.transcript);
        }

        // Show response text
        if (onResponse) {
          onResponse(res.data.response_text);
        }

        // Play response audio
        const responseAudio = `data:audio/mp3;base64,${res.data.response_audio}`;
        setAudioUrl(responseAudio);
        
        // Auto-play
        if (audioRef.current) {
          audioRef.current.src = responseAudio;
          audioRef.current.play();
        }
      };
    } catch (err: any) {
      console.error('Voice processing failed:', err);
      alert(err.response?.data?.error || 'Voice processing failed');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-4 p-4 bg-white rounded-lg shadow">
      <div className="flex gap-2">
        {!isRecording ? (
          <Button onClick={startRecording} disabled={isProcessing}>
            🎤 Start Recording
          </Button>
        ) : (
          <Button onClick={stopRecording} variant="secondary">
            ⏹ Stop Recording
          </Button>
        )}
      </div>

      {isRecording && (
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-600">Recording...</span>
        </div>
      )}

      {isProcessing && (
        <div className="text-sm text-gray-600">Processing voice...</div>
      )}

      {audioUrl && (
        <audio ref={audioRef} controls className="w-full">
          <source src={audioUrl} type="audio/mp3" />
        </audio>
      )}
    </div>
  );
}
