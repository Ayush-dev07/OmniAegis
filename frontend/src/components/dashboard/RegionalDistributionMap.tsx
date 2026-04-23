import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';
import { regionalDistribution } from '@/data/mockData';
import { GlassCard } from '@/components/common/GlassCard';

const fillMap: Record<string, string> = {
  Low: '#14b8a6',
  Medium: '#22d3ee',
  High: '#8b5cf6',
  Critical: '#f97316',
};

function RegionCell(props: any) {
  const { x, y, width, height, name, value, severity } = props;
  const color = fillMap[severity as keyof typeof fillMap] ?? '#22d3ee';

  return (
    <g>
      <rect x={x} y={y} width={width} height={height} rx={18} ry={18} fill={color} fillOpacity={0.22} stroke={color} strokeOpacity={0.45} />
      <text x={x + 14} y={y + 24} fill="#f8fafc" fontSize={14} fontWeight={600}>
        {name}
      </text>
      <text x={x + 14} y={y + 46} fill="#cbd5e1" fontSize={12}>
        {value} alerts
      </text>
      <circle cx={x + width - 20} cy={y + 22} r={6} fill={color} />
    </g>
  );
}

export function RegionalDistributionMap() {
  return (
    <GlassCard className="p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-50">Regional Source Distribution</h2>
          <p className="text-sm text-slate-400">Unauthorized-source heat concentration across monitored territories</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="h-2 w-2 rounded-full bg-teal-400" /> Low
          <span className="h-2 w-2 rounded-full bg-cyan-400" /> Medium
          <span className="h-2 w-2 rounded-full bg-violet-400" /> High
          <span className="h-2 w-2 rounded-full bg-orange-400" /> Critical
        </div>
      </div>

      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <Treemap
            data={regionalDistribution}
            dataKey="value"
            aspectRatio={4 / 3}
            stroke="rgba(148, 163, 184, 0.16)"
            content={<RegionCell />}
          >
            <Tooltip
              contentStyle={{
                background: 'rgba(15, 23, 42, 0.96)',
                border: '1px solid rgba(34, 211, 238, 0.2)',
                borderRadius: 16,
                color: '#e2e8f0',
              }}
              labelStyle={{ color: '#67e8f9' }}
            />
          </Treemap>
        </ResponsiveContainer>
      </div>
    </GlassCard>
  );
}