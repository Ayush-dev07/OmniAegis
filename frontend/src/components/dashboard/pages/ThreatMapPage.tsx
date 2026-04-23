import { RegionalDistributionMap } from '@/components/dashboard/RegionalDistributionMap';
import { GlassCard } from '@/components/common/GlassCard';

export function ThreatMapPage() {
  return (
    <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
      <RegionalDistributionMap />
      <GlassCard className="p-5">
        <h3 className="text-lg font-semibold text-slate-50">Threat Source Notes</h3>
        <div className="mt-4 space-y-3 text-sm text-slate-300">
          <p>Asia Pacific remains the highest-risk corridor with repeated metadata fingerprints across mirrored assets.</p>
          <p>Europe shows elevated brand misuse, primarily through reseller domains and local-language reposting.</p>
          <p>North America continues to present archived-content leakage signals with moderate propagation velocity.</p>
        </div>
      </GlassCard>
    </div>
  );
}
