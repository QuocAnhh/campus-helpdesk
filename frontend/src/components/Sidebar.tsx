import React from 'react';
import { Link } from 'react-router-dom';

const Sidebar: React.FC = () => {
  return (
    <div className="w-64 h-screen bg-gray-800 text-white">
      <div className="p-4 text-xl font-bold">Admin Menu</div>
      <nav>
        <ul>
          <li className="p-4 hover:bg-gray-700">
            <Link to="/admin">Dashboard</Link>
          </li>
          <li className="p-4 hover:bg-gamma-700">
            <Link to="/admin/chat-logs">Chat Logs</Link>
          </li>
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar; 