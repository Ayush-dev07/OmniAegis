'use client';

import { useEffect, useMemo, useState } from 'react';
import DashboardShell from '@/components/DashboardShell';
import OverviewMetrics from '@/components/OverviewMetrics';
import OverviewCards from '@/components/OverviewCards';
import LiveActivityFeed from '@/components/LiveActivityFeed';
import ThreatQueue from '@/components/ThreatQueue';
import HITLApprovalSummary from '@/components/HITLApprovalSummary';
import ContentRegistrationModal from '@/components/ContentRegistrationModal';
import SaliencyDriftViewer, { UMAPPoint } from '@/src/components/phase2/xai/SaliencyDriftViewer';
import FLHealthMonitor, { EdgeNode } from '@/src/components/phase2/fl/FLHealthMonitor';
import HITLDecisionQueue from '@/src/components/phase2/hitl/HITLDecisionQueue';
import { useAuth } from '@/lib/auth-context';

export default function ExecutiveCommandCenter() {
  const { user } = useAuth();
  const [isContentModalOpen, setIsContentModalOpen] = useState(false);
  const xaiPoints = useMemo<UMAPPoint[]>(
    () => [
      { id: 'asset-1', x: 0.12, y: 0.86, label: 'Potential logo spoofing pattern detected.', score: 0.82 },
      { id: 'asset-2', x: 0.27, y: 0.74, label: 'Near-duplicate frame cluster.', score: 0.63 },
      { id: 'asset-3', x: 0.71, y: 0.32, label: 'Low-risk drift segment.', score: 0.34 },
      { id: 'asset-4', x: 0.88, y: 0.21, label: 'Cross-tenant semantic anomaly.', score: 0.76 },
      { id: 'asset-5', x: 0.49, y: 0.57, label: 'Watermark mismatch context.', score: 0.55 },
    ],
    []
  );

  const flNodes = useMemo<EdgeNode[]>(
    () => [
      { id: 'edge-us-east-01', label: 'US-East #01', status: 'training' },
      { id: 'edge-eu-west-02', label: 'EU-West #02', status: 'syncing' },
      { id: 'edge-ap-south-03', label: 'AP-South #03', status: 'idle' },
      { id: 'edge-us-west-04', label: 'US-West #04', status: 'training' },
      { id: 'edge-eu-central-05', label: 'EU-Central #05', status: 'syncing' },
      { id: 'edge-test-06', label: 'Test Node #06', status: 'offline' },
    ],
    []
  );

  useEffect(() => {
    if (!user) {
      return;
    }

    const promptKey = `content-registration-prompt:${user.id}`;
    if (!sessionStorage.getItem(promptKey)) {
      setIsContentModalOpen(true);
      sessionStorage.setItem(promptKey, 'shown');
    }
  }, [user]);

  const handleCloseContentModal = () => {
    setIsContentModalOpen(false);
  };

  return (
    <>
      <DashboardShell>
        <div className="mb-8 rounded-[2rem] border border-cyan-200/70 bg-gradient-to-r from-cyan-50 via-white to-blue-50 p-6 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <p className="text-sm uppercase tracking-[0.28em] text-cyan-700">Content intake</p>
              <h2 className="text-2xl font-bold tracking-tight text-slate-950">Register protected assets from one panel</h2>
              <p className="max-w-2xl text-sm leading-6 text-slate-600">
                Use the content registration popup to submit video, image, or audio assets together with the associated license file.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setIsContentModalOpen(true)}
              className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Open registration popup
            </button>
          </div>
        </div>

        <div className="grid gap-8 xl:grid-cols-[1.3fr_0.7fr]">
          <section className="space-y-8">
            <OverviewMetrics />
            <OverviewCards />
            <LiveActivityFeed />

            <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-8 shadow-sm backdrop-blur-sm">
              <div className="mb-6">
                <p className="text-sm uppercase tracking-[0.28em] text-slate-400">Phase 2 · XAI</p>
                <h2 className="mt-2 text-2xl font-bold text-slate-950">Saliency / Drift Viewer</h2>
              </div>
              <SaliencyDriftViewer points={xaiPoints} />
            </div>

            <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-8 shadow-sm backdrop-blur-sm">
              <div className="mb-6">
                <p className="text-sm uppercase tracking-[0.28em] text-slate-400">Phase 2 · Federated Learning</p>
                <h2 className="mt-2 text-2xl font-bold text-slate-950">Edge Topology Health</h2>
              </div>
              <FLHealthMonitor nodes={flNodes} />
            </div>
          </section>
          <section className="space-y-8">
            <ThreatQueue />

            <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-8 shadow-sm backdrop-blur-sm">
              <div className="mb-6">
                <p className="text-sm uppercase tracking-[0.28em] text-slate-400">Phase 2 · HITL</p>
                <h2 className="mt-2 text-2xl font-bold text-slate-950">Decision Queue (Live)</h2>
              </div>
              <HITLDecisionQueue maxItems={120} />
            </div>

            {/* Admin-only: Approved HITL Decisions */}
            {user?.role === 'admin' && (
              <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-8 shadow-sm backdrop-blur-sm">
                <div className="mb-6">
                  <p className="text-sm uppercase tracking-[0.28em] text-slate-400">HITL Approvals</p>
                  <h2 className="mt-2 text-2xl font-bold text-slate-950">Recent Decisions</h2>
                  <p className="mt-2 text-sm text-slate-600">Approved piracy threat authentications from reviewers</p>
                </div>
                <HITLApprovalSummary />
              </div>
            )}
          </section>
        </div>
      </DashboardShell>

      {user && (
        <ContentRegistrationModal
          isOpen={isContentModalOpen}
          onClose={handleCloseContentModal}
          userId={user.id}
          userName={user.name}
        />
      )}
    </>
  );
}