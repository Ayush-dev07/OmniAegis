import { motion } from 'framer-motion';
import { ChevronRight, ShieldAlert, ShieldCheck, ShieldX } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import { GlassCard } from '@/components/common/GlassCard';
import { StatusBadge } from '@/components/common/StatusBadge';
import type { FeedEntry } from '@/types/dashboard';
import type { Tone } from '@/theme/theme';

const levelStyles = {
  info: { color: 'text-cyan-300', icon: ChevronRight },
  warn: { color: 'text-amber-300', icon: ShieldAlert },
  critical: { color: 'text-rose-300', icon: ShieldX },
  success: { color: 'text-emerald-300', icon: ShieldCheck },
};

const levelToneMap: Record<FeedEntry['level'], Tone> = {
  info: 'cyan',
  warn: 'amber',
  critical: 'rose',
  success: 'emerald',
};

export function LiveFeedLog() {
  const { liveFeed } = useDashboard();

  return (
    <GlassCard className="overflow-hidden p-0">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-50">Live Feed Log</h3>
          <p className="text-xs text-slate-400">Real-time SentinelAgent activity stream</p>
        </div>
        <StatusBadge label="Streaming" tone="emerald" />
      </div>

      <div className="scrollbar-thin max-h-[220px] overflow-y-auto bg-slate-950/60 p-4 font-mono text-xs">
        <motion.div layout className="space-y-2">
          {liveFeed.map((entry) => {
            const style = levelStyles[entry.level];
            const Icon = style.icon;

            return (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start gap-3 rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2"
              >
                <Icon className={`mt-0.5 h-4 w-4 ${style.color}`} />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2 text-slate-400">
                    <span>{entry.timestamp}</span>
                    <StatusBadge label={entry.level} tone={levelToneMap[entry.level]} uppercase />
                  </div>
                  <p className={`mt-1 leading-relaxed ${style.color}`}>{entry.message}</p>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </GlassCard>
  );
}