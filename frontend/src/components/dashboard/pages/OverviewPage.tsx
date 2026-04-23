import { KpiGrid } from '@/components/dashboard/KpiGrid';
import { ThreatTrendsChart } from '@/components/dashboard/ThreatTrendsChart';
import { RegionalDistributionMap } from '@/components/dashboard/RegionalDistributionMap';
import { LiveFeedLog } from '@/components/common/LiveFeedLog';

export function OverviewPage() {
  return (
    <>
      <KpiGrid />
      <div className="grid items-stretch gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <ThreatTrendsChart />
        <RegionalDistributionMap />
      </div>
      <LiveFeedLog />
    </>
  );
}
