'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import axiosInstance from '@/lib/axios';
import { MeetingProvider, MeetingConsumer, useMeeting, useParticipant } from '@videosdk.live/react-sdk';

function ParticipantView({ participantId }: { participantId: string }) {
  const { webcamStream, micStream, webcamOn, micOn, isLocal } = useParticipant(participantId);
  return (
    <div className="border rounded p-2">
      <div className="text-xs mb-1">{isLocal ? 'You' : participantId}</div>
      <div className="bg-black aspect-video rounded overflow-hidden">
        {/* Videosdk provides MediaStream - create <video> refs or use their components */}
        {/* For brevity, rely on MeetingConsumer’s examples in docs */}
      </div>
      <div className="text-xs mt-1">Mic: {micOn ? 'On' : 'Off'} • Cam: {webcamOn ? 'On' : 'Off'}</div>
    </div>
  );
}

function Controls() {
  const { leave, toggleMic, toggleWebcam, enableScreenShare, disableScreenShare, localScreenShareOn } = useMeeting();
  return (
    <div className="flex gap-2 mt-3">
      <button className="px-3 py-2 bg-gray-200 rounded" onClick={() => toggleMic()}>Mic</button>
      <button className="px-3 py-2 bg-gray-200 rounded" onClick={() => toggleWebcam()}>Camera</button>
      {!localScreenShareOn ? (
        <button className="px-3 py-2 bg-gray-200 rounded" onClick={() => enableScreenShare()}>Share Screen</button>
      ) : (
        <button className="px-3 py-2 bg-gray-200 rounded" onClick={disableScreenShare}>Stop Share</button>
      )}
      <button className="px-3 py-2 bg-red-500 text-white rounded" onClick={leave}>Leave</button>
    </div>
  );
}

export default function LiveSessionPage() {
  const params = useParams();
  const router = useRouter();
  const [meetingId, setMeetingId] = useState<string>('');
  const [token, setToken] = useState<any>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await axiosInstance.post(`/courses/rtc/session/${params.id}/join-token/`);
        setMeetingId(res.data.roomId);
        setToken(res.data.token);
      } catch (e) {
        router.push('/dashboard/student');
      }
    };
    load();
  }, [params, router]);

  if (!meetingId || !token) return <div className="p-6">Loading...</div>;

  return (
    <MeetingProvider
      config={{
        meetingId,
        micEnabled: true,
        webcamEnabled: true,
        name: 'Participant',
        debugMode: false,
      }}
      token={token.apiKey}  // Videosdk allows apiKey init; token abstraction shown earlier
    >
      <MeetingConsumer>
        {({ participants }: any) => (
          <div className="p-4">
            <h2 className="text-xl font-bold">Live Session</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-3">
              {Array.from(participants.keys() as IterableIterator<string>).map((pId: string) => (
                <ParticipantView key={pId} participantId={pId} />
              ))}
            </div>
            <Controls />
          </div>
        )}
      </MeetingConsumer>
    </MeetingProvider>
  );
}
