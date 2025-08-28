import { GraduationCap, Settings, LogOut, Ticket, User, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

interface UserLayoutProps {
  children: React.ReactNode;
}

export const UserLayout = ({ children }: UserLayoutProps) => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gradient-chat flex flex-col">
      {/* Header */}
      <header className="bg-card border-b border-border shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-primary rounded-xl flex items-center justify-center">
              <GraduationCap className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">Campus Helpdesk</h1>
              <p className="text-sm text-muted-foreground">
                Welcome, {user?.full_name || user?.username}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Link to="/">
              <Button 
                variant={isActive('/') ? 'default' : 'ghost'} 
                size="sm"
              >
                <MessageSquare className="h-4 w-4 mr-2" />
                Chat
              </Button>
            </Link>
            <Link to="/self-service">
              <Button 
                variant={isActive('/self-service') ? 'default' : 'ghost'} 
                size="sm"
              >
                <User className="h-4 w-4 mr-2" />
                Self-Service
              </Button>
            </Link>
            <Link to="/tickets">
              <Button 
                variant={isActive('/tickets') ? 'default' : 'ghost'} 
                size="sm"
              >
                <Ticket className="h-4 w-4 mr-2" />
                Support Tickets
              </Button>
            </Link>
            {user?.role === 'admin' && (
              <Link to="/admin">
                <Button 
                  variant={isActive('/admin') ? 'default' : 'ghost'} 
                  size="sm"
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Admin
                </Button>
              </Link>
            )}
            <Button variant="outline" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
};
