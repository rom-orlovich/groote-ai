import { clsx } from "clsx";
import { type ReactNode, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { TaskStatusModal } from "../components/TaskStatusModal";
import { Header } from "../components/ui/Header";
import { Sidebar } from "../components/ui/Sidebar";

interface DashboardLayoutProps {
  children: ReactNode;
  headerSlot?: ReactNode;
  sidebarSlot?: ReactNode;
}

export function DashboardLayout({ children, headerSlot, sidebarSlot }: DashboardLayoutProps) {
  const location = useLocation();
  const isChat = location.pathname === "/chat";
  const isSetup = location.pathname === "/install" || location.pathname === "/settings/ai-provider";
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    setSidebarOpen(true);
  }, []);

  if (isSetup) {
    return (
      <div className="h-screen flex flex-col bg-background-app transition-colors duration-300">
        <div className="flex-1 flex items-center justify-center overflow-y-auto p-4">
          <div className="w-full max-w-2xl">{children}</div>
        </div>
        <TaskStatusModal />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background-app transition-colors duration-300">
      {headerSlot || (
        <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} isSidebarOpen={sidebarOpen} />
      )}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Monitoring Grid Overlay */}
        <div className="monitoring-grid" />

        {sidebarSlot || <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />}
        <main
          className={clsx(
            "flex-1 relative z-10 animate-in fade-in slide-in-from-bottom-2 duration-700",
            isChat ? "overflow-hidden p-2 md:p-4" : "overflow-y-auto p-2 md:p-8",
          )}
        >
          <div
            className={clsx(
              "mx-auto",
              isChat ? "h-full max-w-full space-y-0" : "max-w-7xl space-y-8",
            )}
          >
            {children}
          </div>
        </main>
      </div>
      <TaskStatusModal />
    </div>
  );
}
