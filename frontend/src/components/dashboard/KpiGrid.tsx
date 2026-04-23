import { ArrowDownRight, ArrowUpRight, AlertTriangle, ShieldCheck, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { kpiStats } from '@/data/mockData';
import { GlassCard } from '@/components/common/GlassCard';

const iconMap = {
  ShieldCheck,
  AlertTriangle,
  Sparkles,
};

export function KpiGrid() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {kpiStats.map((stat, index) => {
        const Icon = iconMap[stat.icon as keyof typeof iconMap];

        return (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: index * 0.08 }}
          >
            <GlassCard className="h-full p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-50">{stat.value}</p>
                </div>
                <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-3 text-cyan-300 shadow-neon">
                  <Icon className="h-5 w-5" />
                </div>
              </div>

              <div className="mt-5 flex items-center justify-between gap-3 text-sm">
                <span className="inline-flex items-center gap-1 text-emerald-300">
                  {stat.trend === 'up' ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                  {stat.delta}
                </span>
                <span className="rounded-full bg-white/5 px-3 py-1 text-xs text-slate-400">Real-time</span>
              </div>
            </GlassCard>
          </motion.div>
        );
      })}
    </div>
  );
}