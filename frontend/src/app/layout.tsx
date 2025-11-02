import ChatWidget from '@/components/chatbot/ChatWidget';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
        <ChatWidget />  {/* Add this */}
      </body>
    </html>
  );
}
