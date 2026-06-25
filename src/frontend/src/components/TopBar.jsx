import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  LogOut, Menu, Settings, FileText, Monitor, Shield
} from 'lucide-react';

export default function TopBar({ sidebarOpen, onToggleSidebar }) {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="h-14 bg-noc-surface border-b border-noc-border flex items-center px-4 shrink-0 z-20">
      {/* Left: Menu toggle + logo */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="btn-ghost p-2 rounded-lg"
          title="Toggle sidebar"
        >
          <Menu size={18} />
        </button>
        <div className="flex items-center gap-2">
          <Monitor size={20} className="text-noc-accent" />
          <span className="font-bold text-lg tracking-tight">
            Node<span className="text-noc-accent">Ping</span>
          </span>
        </div>
      </div>

      {/* Right: nav + user */}
      <div className="ml-auto flex items-center gap-2">
        {isAdmin && (
          <>
            <button
              onClick={() => navigate('/settings')}
              className="btn-ghost flex items-center gap-1.5 text-sm"
            >
              <Settings size={16} />
              <span className="hidden sm:inline">Settings</span>
            </button>
            <button
              onClick={() => navigate('/reports')}
              className="btn-ghost flex items-center gap-1.5 text-sm"
            >
              <FileText size={16} />
              <span className="hidden sm:inline">Reports</span>
            </button>
          </>
        )}

        {!isAdmin && (
          <button
            onClick={() => navigate('/reports')}
            className="btn-ghost flex items-center gap-1.5 text-sm"
          >
            <FileText size={16} />
            <span className="hidden sm:inline">Reports</span>
          </button>
        )}

        <div className="h-6 w-px bg-noc-border mx-1" />

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            {isAdmin && <Shield size={14} className="text-noc-accent" />}
            <span className="text-sm text-noc-muted">{user?.username}</span>
            <span className="text-xs bg-noc-card px-1.5 py-0.5 rounded text-noc-dim">
              {user?.role}
            </span>
          </div>
          <button onClick={handleLogout} className="btn-ghost p-2" title="Logout">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}
