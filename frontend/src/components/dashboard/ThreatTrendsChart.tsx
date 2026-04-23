import { ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Line } from 'recharts';
import { motion } from 'framer-motion';
import { threatTrends } from '@/data/mockData';
import { GlassCard } from '@/components/common/GlassCard';

export function ThreatTrendsChart() {
  return (
    <GlassCard className="p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-50">Threat Attempts Over Time</h2>
          <p className="text-sm text-slate-400">Trendline of detected and blocked attempts across the last cycle</p>
        </div>
        <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300">
          Recharts line chart
        </span>
      </div>

      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={threatTrends} margin={{ left: 8, right: 8, top: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="attemptsStroke" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22d3ee" />
                <stop offset="100%" stopColor="#8b5cf6" />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.15)" strokeDasharray="4 4" />
            <XAxis dataKey="time" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                background: 'rgba(15, 23, 42, 0.96)',
                border: '1px solid rgba(34, 211, 238, 0.2)',
                borderRadius: 16,
                color: '#e2e8f0',
              }}
              labelStyle={{ color: '#67e8f9' }}
              cursor={{ stroke: 'rgba(34, 211, 238, 0.35)' }}
            />
            <Line type="monotone" dataKey="attempts" stroke="url(#attemptsStroke)" strokeWidth={3} dot={false} />
            <Line type="monotone" dataKey="blocked" stroke="#10b981" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </motion.div>
    </GlassCard>
  );
}