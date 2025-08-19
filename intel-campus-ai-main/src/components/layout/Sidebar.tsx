import { NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, GraduationCap } from 'lucide-react';

const navigation = [
  {
    name: 'Dashboard',
    href: '/admin',
    icon: LayoutDashboard,
  },
  {
    name: 'Chat Logs',
    href: '/admin/chat-logs',
    icon: MessageSquare,
  },
];

export const Sidebar = () => {
  return (
    <div className="w-64 bg-card border-r border-border h-full">
      <div className="p-6 border-b border-border">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
            <GraduationCap className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">Campus Helpdesk</h1>
            <p className="text-sm text-muted-foreground">Admin Panel</p>
          </div>
        </div>
      </div>
      
      <nav className="p-4">
        <div className="space-y-2">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `sidebar-item ${isActive ? 'sidebar-item-active' : ''}`
              }
              end
            >
              <item.icon className="h-5 w-5 mr-3" />
              {item.name}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
};