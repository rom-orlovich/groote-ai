import type { ReactNode } from "react";

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <div className="monitoring-grid" />
      <header className="border-b border-panel-border p-4">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <div className="w-8 h-8 bg-cta flex items-center justify-center">
            <span className="text-white font-heading text-xs font-bold">G</span>
          </div>
          <div>
            <h1 className="text-xs font-heading font-bold tracking-widest">GROOTE_AI</h1>
            <p className="text-[9px] font-heading text-gray-500">ADMIN_SETUP</p>
          </div>
        </div>
      </header>
      <main className="max-w-4xl mx-auto p-6">{children}</main>
    </div>
  );
}
