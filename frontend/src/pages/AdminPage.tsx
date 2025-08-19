import React from 'react';
import Sidebar from '../components/Sidebar';

const AdminPage: React.FC = () => {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-4">
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <p>Welcome to the admin dashboard.</p>
      </main>
    </div>
  );
};

export default AdminPage; 