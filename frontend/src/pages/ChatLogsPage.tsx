import React from 'react';
import Sidebar from '../components/Sidebar';

const ChatLogsPage: React.FC = () => {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-4">
        <h1 className="text-2xl font-bold">Chat Logs</h1>
        <p>This is where the chat logs will be displayed.</p>
      </main>
    </div>
  );
};

export default ChatLogsPage; 