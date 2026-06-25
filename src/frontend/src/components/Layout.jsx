import { Outlet } from 'react-router-dom';
import TopBar from './TopBar';
import Sidebar from './Sidebar';
import Toast from './Toast';
import { useState } from 'react';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedTarget, setSelectedTarget] = useState(null);

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-noc-bg">
      <TopBar
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
      />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          open={sidebarOpen}
          selectedTarget={selectedTarget}
          onSelectTarget={setSelectedTarget}
        />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet context={{ selectedTarget, setSelectedTarget, sidebarOpen }} />
        </main>
      </div>
      <Toast />
    </div>
  );
}
