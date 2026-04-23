import { GlassCard } from '@/components/common/GlassCard';
import { StatusBadge } from '@/components/common/StatusBadge';
import { apiEndpoints } from '@/data/mockData';

const statusToneMap = {
  '200': 'emerald',
  '201': 'cyan',
  '429': 'amber',
  '503': 'rose',
} as const;

export function ApiConfigPage() {
  return (
    <GlassCard className="overflow-hidden p-0">
      <div className="border-b border-white/10 p-4">
        <h3 className="text-sm font-semibold text-slate-50">API Endpoints</h3>
        <p className="text-xs text-slate-400">Operational endpoints used by SentinelAgent enforcement workflows</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/[0.03] text-xs uppercase tracking-[0.25em] text-slate-500">
            <tr>
              <th className="px-4 py-3">Method</th>
              <th className="px-4 py-3">Endpoint</th>
              <th className="px-4 py-3">Latency</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {apiEndpoints.map((endpoint) => (
              <tr key={endpoint.endpoint} className="text-slate-300">
                <td className="px-4 py-4 font-medium text-cyan-300">{endpoint.method}</td>
                <td className="px-4 py-4">{endpoint.endpoint}</td>
                <td className="px-4 py-4">{endpoint.latency}</td>
                <td className="px-4 py-4">
                  <StatusBadge label={endpoint.status} tone={statusToneMap[endpoint.status]} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </GlassCard>
  );
}
