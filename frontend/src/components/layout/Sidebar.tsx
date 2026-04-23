import { AnimatePresence, motion } from 'framer-motion';
import { Activity, Cpu, LayoutDashboard, ShieldAlert, Settings2, X, type LucideIcon } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import type { ViewKey } from '@/types/dashboard';
import { GlassCard } from '@/components/common/GlassCard';

const navItems: Array<{ key: ViewKey; label: string; icon: LucideIcon; helper: string }> = [
  { key: 'overview', label: 'Dashboard Overview', icon: LayoutDashboard, helper: 'Posture summary' },
  { key: 'monitoring', label: 'Active Monitoring', icon: ShieldAlert, helper: 'The Queue' },
  { key: 'threat-map', label: 'Threat Map', icon: Activity, helper: 'Regional source heat' },
  { key: 'health', label: 'System Health', icon: Cpu, helper: 'Log / Audit' },
  { key: 'api', label: 'API Configuration', icon: Settings2, helper: 'Policy integration' },
];

interface SidebarProps {
  mobileOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ mobileOpen, onClose }: SidebarProps) {
  const { currentView, setCurrentView } = useDashboard();

  const content = (
    <div className="flex h-full w-[300px] flex-col gap-6 p-4 lg:w-full lg:p-6">
      <div className="flex items-center justify-between lg:justify-start">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-cyan-300/80">SentinelAgent</p>
          <h1 className="mt-1 text-xl font-semibold text-slate-50">Security Gateway</h1>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-xl border border-white/10 bg-white/5 p-2 text-slate-300 lg:hidden"
          aria-label="Close sidebar"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <GlassCard className="p-2">
        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = currentView === item.key;

            return (
              <button
                key={item.key}
                type="button"
                onClick={() => {
                  setCurrentView(item.key);
                  onClose();
                }}
                className={[
                  'flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition-all',
                  active
                    ? 'bg-cyan-400/15 text-cyan-100 shadow-neon'
                    : 'text-slate-300 hover:bg-white/5 hover:text-slate-50',
                ].join(' ')}
              >
                <span className={['rounded-lg p-2', active ? 'bg-cyan-400/20' : 'bg-white/5'].join(' ')}>
                  <Icon className="h-4 w-4" />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-medium">{item.label}</span>
                  <span className="block text-xs text-slate-400">{item.helper}</span>
                </span>
              </button>
            );
          })}
        </nav>
      </GlassCard>

      <GlassCard className="mt-auto p-4 text-sm text-slate-300">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">System posture</p>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <div>
            <p className="text-slate-500">Nodes online</p>
            <p className="text-lg font-semibold text-emerald-300">48/48</p>
          </div>
          <div>
            <p className="text-slate-500">Policy lag</p>
            <p className="text-lg font-semibold text-cyan-300">18 ms</p>
          </div>
        </div>
      </GlassCard>
    </div>
  );

  return (
    <>
      <aside className="hidden border-r border-white/10 bg-slate-950/60 lg:flex lg:w-[320px] lg:flex-col">
        {content}
      </aside>

      <AnimatePresence>
        {mobileOpen ? (
          <motion.aside
            initial={{ x: -360, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -360, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 260, damping: 28 }}
            className="fixed inset-y-0 left-0 z-50 w-[90vw] max-w-[320px] border-r border-white/10 bg-slate-950/95 backdrop-blur-xl lg:hidden"
          >
            {content}
          </motion.aside>
        ) : null}
      </AnimatePresence>
    </>
  );
}