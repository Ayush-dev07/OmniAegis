import { useDashboard } from '@/context/DashboardContext';
import { GlassCard } from '@/components/common/GlassCard';
import { StatusBadge } from '@/components/common/StatusBadge';

export function MonitoringPage() {
  const { filteredThreats, selectedThreat, setSelectedThreat } = useDashboard();

  return (
    <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
      <GlassCard className="min-w-0 p-0">
        <div className="border-b border-white/10 p-4">
          <h3 className="text-sm font-semibold text-slate-50">Potential Threat Queue</h3>
          <p className="text-xs text-slate-400">Select an item to open the action card panel</p>
        </div>
        <div className="divide-y divide-white/5">
          {filteredThreats.map((threat) => {
            const isActive = selectedThreat?.id === threat.id;
            return (
              <button
                key={threat.id}
                type="button"
                onClick={() => setSelectedThreat(threat)}
                className={[
                  'w-full px-4 py-4 text-left transition hover:bg-white/[0.03]',
                  isActive ? 'bg-cyan-400/10' : '',
                ].join(' ')}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-slate-50">{threat.title}</p>
                    <p className="mt-1 text-sm text-slate-400">{threat.assetName}</p>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-400">
                      <StatusBadge label={threat.category} tone="neutral" />
                      <StatusBadge label={threat.region} tone="cyan" />
                      <StatusBadge label={threat.status} tone="amber" />
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-slate-50">{threat.riskScore}</p>
                    <p className="text-xs text-slate-500">risk</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </GlassCard>

      <GlassCard className="min-w-0 p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-50">Queue Intelligence</h3>
            <p className="text-xs text-slate-400">Triage context and explainability reference</p>
          </div>
          <StatusBadge label="HITL active" tone="cyan" />
        </div>
        {selectedThreat ? (
          <div className="mt-4 space-y-4 text-sm text-slate-300">
            <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
              <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Explainability</p>
              <p className="mt-2 leading-6">{selectedThreat.explainability}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Source</p>
                <p className="mt-2 break-words text-slate-200">{selectedThreat.source}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Region</p>
                <p className="mt-2 text-slate-200">{selectedThreat.region}</p>
              </div>
            </div>
            <p className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-xs text-slate-400">
              The action card is rendered as a modal panel with animated transitions. Approval, takedown, and escalation actions are wired to mocked state updates.
            </p>
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-400">No item selected.</p>
        )}
      </GlassCard>
    </div>
  );
}
