import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { UserHeader } from './UserHeader';

interface AdminLayoutProps {
  children: ReactNode;
}

export const AdminLayout = ({ children }: AdminLayoutProps) => {
  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <UserHeader />
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
      </div>
    </div>
  );
};