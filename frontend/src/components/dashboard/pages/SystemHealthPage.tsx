import { GlassCard } from '@/components/common/GlassCard';
import { StatusBadge } from '@/components/common/StatusBadge';
import { healthMetrics } from '@/data/mockData';
import { healthToneMap } from '@/theme/theme';

export function SystemHealthPage() {
  return (
    <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
      <GlassCard className="p-5">
        <h3 className="text-lg font-semibold text-slate-50">Platform Health</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {healthMetrics.map((metric) => (
            <div key={metric.label} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm text-slate-400">{metric.label}</p>
              <p className="mt-2 text-2xl font-semibold text-slate-50">{metric.value}</p>
              <div className="mt-2">
                <StatusBadge label={metric.status} tone={healthToneMap[metric.status]} uppercase className="tracking-[0.2em]" />
              </div>
            </div>
          ))}
        </div>
      </GlassCard>

      <GlassCard className="overflow-hidden p-0">
        <div className="border-b border-white/10 p-4">
          <h3 className="text-sm font-semibold text-slate-50">Audit Trail</h3>
          <p className="text-xs text-slate-400">Recent platform events and compliance checkpoints</p>
        </div>
        <div className="divide-y divide-white/5 text-sm">
          {['Policy bundle signed', 'Model checksum validated', 'Archive sync completed', 'Queue worker restarted'].map((item, index) => (
            <div key={item} className="flex items-center justify-between px-4 py-4">
              <span className="text-slate-300">{item}</span>
              <span className="text-xs text-slate-500">0{index + 1}:42</span>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}
