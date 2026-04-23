import { AnimatePresence, motion } from 'framer-motion';
import { Bell, Filter, LayoutGrid, ShieldCheck } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopBar } from '@/components/layout/TopBar';
import { ActionCard } from '@/components/monitoring/ActionCard';
import { StatusBadge } from '@/components/common/StatusBadge';
import { pageCopy } from '@/components/dashboard/pageMeta';
import { OverviewPage } from '@/components/dashboard/pages/OverviewPage';
import { MonitoringPage } from '@/components/dashboard/pages/MonitoringPage';
import { ThreatMapPage } from '@/components/dashboard/pages/ThreatMapPage';
import { SystemHealthPage } from '@/components/dashboard/pages/SystemHealthPage';
import { ApiConfigPage } from '@/components/dashboard/pages/ApiConfigPage';
import type { ThreatItem } from '@/types/dashboard';
import { useState } from 'react';

function PageContent() {
  const { currentView } = useDashboard();

  return (
    <AnimatePresence mode="wait">
      <motion.section
        key={currentView}
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -18 }}
        transition={{ duration: 0.25 }}
        className="space-y-6"
      >
        {currentView === 'overview' ? <OverviewPage /> : null}
        {currentView === 'monitoring' ? <MonitoringPage /> : null}
        {currentView === 'threat-map' ? <ThreatMapPage /> : null}
        {currentView === 'health' ? <SystemHealthPage /> : null}
        {currentView === 'api' ? <ApiConfigPage /> : null}
      </motion.section>
    </AnimatePresence>
  );
}

export function Dashboard() {
  const { currentView, selectedThreat, setSelectedThreat, pushFeedEntry } = useDashboard();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const heading = pageCopy[currentView];

  const handleAction = (threat: ThreatItem, action: string) => {
    pushFeedEntry({
      id: crypto.randomUUID(),
      timestamp: new Date().toLocaleTimeString([], { hour12: false }),
      message: `${action} recorded for ${threat.id} (${threat.title}).`,
      level: action === 'Escalation' ? 'critical' : action === 'Takedown' ? 'warn' : 'success',
    });
    setSelectedThreat(null);
  };

  return (
    <div className="relative isolate min-h-screen overflow-x-hidden bg-slate-950 text-slate-100">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-grid-faint bg-[length:28px_28px] opacity-30" />
      <div className="flex min-h-screen flex-col lg:flex-row">
        <Sidebar mobileOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <div className="relative z-10 flex min-w-0 flex-1 flex-col">
          <TopBar onMenuOpen={() => setSidebarOpen(true)} />

          <main className="flex-1 px-4 py-6 lg:px-6">
            <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <div className="mb-2">
                  <StatusBadge label="Global filters applied" tone="cyan" icon={<Filter className="h-3.5 w-3.5" />} />
                </div>
                <h2 className="text-2xl font-semibold text-slate-50 lg:text-3xl">{heading.title}</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{heading.subtitle}</p>
              </div>

              <div className="grid grid-cols-1 gap-3 text-center text-xs text-slate-400 min-[520px]:grid-cols-3 sm:w-[360px]">
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                  <Bell className="mx-auto mb-2 h-4 w-4 text-cyan-300" />
                  Alerts live
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                  <LayoutGrid className="mx-auto mb-2 h-4 w-4 text-violet-300" />
                  Multi-panel
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                  <ShieldCheck className="mx-auto mb-2 h-4 w-4 text-emerald-300" />
                  WCAG aware
                </div>
              </div>
            </div>

            <PageContent />
          </main>
        </div>
      </div>

      <ActionCard
        threat={selectedThreat}
        onClose={() => setSelectedThreat(null)}
        onApprove={(threat) => handleAction(threat, 'Whitelist')}
        onTakedown={(threat) => handleAction(threat, 'Takedown')}
        onEscalate={(threat) => handleAction(threat, 'Escalation')}
      />

      {sidebarOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-slate-950/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close sidebar backdrop"
        />
      ) : null}
    </div>
  );
}