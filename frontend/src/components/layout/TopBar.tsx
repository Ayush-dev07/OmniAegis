import { CalendarRange, Menu, Search, Shield } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import { GlassCard } from '@/components/common/GlassCard';
import { StatusBadge } from '@/components/common/StatusBadge';

interface TopBarProps {
  onMenuOpen: () => void;
}

export function TopBar({ onMenuOpen }: TopBarProps) {
  const { searchTerm, setSearchTerm, dateRange, setDateRange } = useDashboard();

  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-slate-950/70 backdrop-blur-xl">
      <div className="flex flex-col gap-3 px-4 py-4 lg:px-6">
        <div className="flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={onMenuOpen}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 lg:hidden"
            aria-label="Open sidebar"
          >
            <Menu className="h-4 w-4" />
            Menu
          </button>

          <div className="hidden items-center gap-3 lg:flex">
            <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-2 text-cyan-300 shadow-neon">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-cyan-300/70">SentinelAgent</p>
              <p className="text-sm text-slate-400">Digital Asset Protection and Security Gateway</p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400">
            <StatusBadge label="Live" tone="emerald" />
            <span className="hidden sm:inline">Policy sync healthy</span>
          </div>
        </div>

        <GlassCard className="grid gap-3 p-3 lg:grid-cols-[1fr_280px] lg:items-center">
          <label className="flex items-center gap-3 rounded-xl border border-white/10 bg-slate-900/80 px-3 py-2 text-slate-300 focus-within:border-cyan-400/40">
            <Search className="h-4 w-4 text-cyan-300" />
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search threats, assets, regions, or IDs"
              className="w-full bg-transparent text-sm outline-none placeholder:text-slate-500"
            />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 rounded-xl border border-white/10 bg-slate-900/80 px-3 py-2 text-xs text-slate-400">
              <CalendarRange className="h-4 w-4 text-cyan-300" />
              <input
                type="date"
                value={dateRange.start}
                onChange={(event) => setDateRange({ ...dateRange, start: event.target.value })}
                className="w-full bg-transparent text-sm text-slate-100 outline-none"
                aria-label="Start date"
              />
            </label>

            <label className="flex items-center gap-2 rounded-xl border border-white/10 bg-slate-900/80 px-3 py-2 text-xs text-slate-400">
              <CalendarRange className="h-4 w-4 text-cyan-300" />
              <input
                type="date"
                value={dateRange.end}
                onChange={(event) => setDateRange({ ...dateRange, end: event.target.value })}
                className="w-full bg-transparent text-sm text-slate-100 outline-none"
                aria-label="End date"
              />
            </label>
          </div>
        </GlassCard>
      </div>
    </header>
  );
}