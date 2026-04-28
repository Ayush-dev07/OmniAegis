'use client';

import React, { useState } from 'react';
import { MainLayout } from '@/components/layout';
import {
  ConfidenceBadge,
  StatusChip,
  Button,
  DataTable,
  Modal,
} from '@/components/ui';

interface AuditRow {
  id: string;
  assetId: string;
  decision: 'approved' | 'rejected' | 'pending';
  confidence: number;
  policy: string;
  timestamp: string;
}

const DEMO_AUDITS: AuditRow[] = [
  {
    id: 'AUDIT-001',
    assetId: 'img_47f3a2',
    decision: 'approved',
    confidence: 0.87,
    policy: 'ContentV3',
    timestamp: '2024-04-28 09:42',
  },
  {
    id: 'AUDIT-002',
    assetId: 'img_56f4b3',
    decision: 'rejected',
    confidence: 0.15,
    policy: 'ContentV3',
    timestamp: '2024-04-28 08:20',
  },
  {
    id: 'AUDIT-003',
    assetId: 'img_65f5c4',
    decision: 'pending',
    confidence: 0.52,
    policy: 'PolicyV2',
    timestamp: '2024-04-28 07:15',
  },
];

export default function OverviewPage() {
  const [selectedAudit, setSelectedAudit] = useState<AuditRow | null>(null);
  const [showModal, setShowModal] = useState(false);

  return (
    <MainLayout
      breadcrumb={[{ label: 'Overview' }]}
      contextPanelTitle={selectedAudit ? `Audit ${selectedAudit.id}` : 'Details'}
      contextPanelContent={
        selectedAudit && (
          <div className="space-y-4">
            <div>
              <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold">
                Asset ID
              </p>
              <p className="text-sm text-text-primary font-mono">{selectedAudit.assetId}</p>
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold">
                Confidence
              </p>
              <div className="mt-1">
                <ConfidenceBadge value={selectedAudit.confidence} />
              </div>
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold">
                Policy
              </p>
              <p className="text-sm text-text-primary">{selectedAudit.policy}</p>
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold">
                Status
              </p>
              <div className="mt-2">
                <StatusChip status={selectedAudit.decision} />
              </div>
            </div>
          </div>
        )
      }
      contextPanelActions={
        selectedAudit && (
          <>
            <Button variant="secondary" size="sm" onClick={() => setSelectedAudit(null)}>
              Close
            </Button>
            <Button size="sm" onClick={() => setShowModal(true)}>
              View Details
            </Button>
          </>
        )
      }
      isContextPanelOpen={!!selectedAudit}
      onContextPanelClose={() => setSelectedAudit(null)}
    >
      {/* Main Content */}
      <div className="space-y-8">
        {/* Hero Section */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold text-text-primary">Overview</h1>
          <p className="text-lg text-text-secondary">
            Monitor ML model audits, decisions, and explainability metrics
          </p>
        </div>

        {/* KPI Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Ingested Today', value: '14,302', icon: '📥' },
            { label: 'Decisions Made', value: '9,847', icon: '✓' },
            { label: 'HITL Queue', value: '12', icon: '👥' },
            { label: 'Privacy Budget', value: 'ε: 0.73', icon: '🔒' },
          ].map((metric) => (
            <div
              key={metric.label}
              className="p-6 rounded-lg border border-border-default bg-surface-secondary hover:bg-surface-tertiary transition-colors duration-fast"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-text-secondary uppercase font-semibold letter-spacing-wide">
                    {metric.label}
                  </p>
                  <p className="text-3xl font-bold text-text-primary mt-2">{metric.value}</p>
                </div>
                <span className="text-3xl">{metric.icon}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Demo Buttons */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-text-primary">Component Examples</h2>

          <div className="space-y-3">
            <div>
              <h3 className="text-sm font-medium text-text-secondary mb-3">Confidence Badges</h3>
              <div className="flex items-center gap-6 p-4 bg-surface-secondary rounded-lg border border-border-default">
                <div>
                  <p className="text-xs text-text-secondary mb-2">High (≥0.80)</p>
                  <ConfidenceBadge value={0.87} />
                </div>
                <div>
                  <p className="text-xs text-text-secondary mb-2">Mid (0.20–0.79)</p>
                  <ConfidenceBadge value={0.45} />
                </div>
                <div>
                  <p className="text-xs text-text-secondary mb-2">Low (&lt;0.20)</p>
                  <ConfidenceBadge value={0.12} />
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-text-secondary mb-3">Status Chips</h3>
              <div className="flex flex-wrap items-center gap-3 p-4 bg-surface-secondary rounded-lg border border-border-default">
                <StatusChip status="approved" />
                <StatusChip status="rejected" />
                <StatusChip status="pending" />
                <StatusChip status="flagged" />
                <StatusChip status="anchored" />
                <StatusChip status="reviewing" />
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-text-secondary mb-3">Buttons</h3>
              <div className="flex flex-wrap items-center gap-3 p-4 bg-surface-secondary rounded-lg border border-border-default">
                <Button variant="primary" size="md">
                  Primary
                </Button>
                <Button variant="secondary" size="md">
                  Secondary
                </Button>
                <Button variant="danger" size="md">
                  Danger
                </Button>
                <Button variant="ghost" size="md">
                  Ghost
                </Button>
                <Button disabled size="md">
                  Disabled
                </Button>
                <Button isLoading size="md">
                  Loading
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Audit Table */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-text-primary">Recent Audits</h2>
          <DataTable<AuditRow>
            columns={[
              {
                key: 'id',
                label: 'ID',
                sortable: true,
                width: '140px',
                render: (val) => (
                  <code className="text-xs font-mono text-accent">{val}</code>
                ),
              },
              {
                key: 'assetId',
                label: 'Asset ID',
                sortable: true,
                render: (val) => (
                  <code className="text-xs font-mono text-text-secondary">{val}</code>
                ),
              },
              {
                key: 'confidence',
                label: 'Confidence',
                sortable: true,
                render: (val) => <ConfidenceBadge value={val} size="sm" />,
              },
              {
                key: 'decision',
                label: 'Decision',
                sortable: true,
                render: (val) => <StatusChip status={val} size="sm" />,
              },
              {
                key: 'policy',
                label: 'Policy',
                sortable: true,
              },
              {
                key: 'timestamp',
                label: 'Timestamp',
                sortable: true,
                render: (val) => (
                  <span className="text-xs text-text-secondary">{val}</span>
                ),
              },
            ]}
            rows={DEMO_AUDITS}
            onRowClick={(row) => setSelectedAudit(row)}
          />
        </div>

        {/* Modal Button */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-text-primary">Modal Example</h2>
          <Button onClick={() => setShowModal(true)}>Open Modal</Button>
        </div>
      </div>

      {/* Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Audit Details"
        size="md"
        actions={
          <>
            <Button variant="secondary" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button onClick={() => setShowModal(false)}>Confirm</Button>
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-sm text-text-secondary">
            This is a modal dialog showing the details of the selected audit record.
          </p>
          <div className="p-4 bg-surface-tertiary rounded-lg border border-border-default">
            <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold mb-2">
              Audit Information
            </p>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-text-secondary">ID:</span>{' '}
                <code className="text-accent font-mono">AUDIT-001</code>
              </div>
              <div>
                <span className="text-text-secondary">Status:</span>{' '}
                <span>✓ APPROVED</span>
              </div>
              <div>
                <span className="text-text-secondary">Confidence:</span> 87%
              </div>
            </div>
          </div>
        </div>
      </Modal>
    </MainLayout>
  );
}
