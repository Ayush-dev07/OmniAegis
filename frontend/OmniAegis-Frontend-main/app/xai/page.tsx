'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { MainLayout } from '@/components/layout';
import { Button, Input } from '@/components/ui';

interface XAIRecord {
  id: string;
  assetId: string;
  assetType: 'image' | 'video' | 'audio' | 'text';
  model: string;
  prediction: string;
  confidence: number;
  timestamp: string;
  explanationMethods: ('saliency' | 'gradient' | 'neighbors' | 'influence')[];
}

const DEMO_RECORDS: XAIRecord[] = [
  {
    id: 'XAI-2024-0001',
    assetId: 'img_47f3a2b9',
    assetType: 'image',
    model: 'v3.2.1',
    prediction: 'Approved',
    confidence: 0.92,
    timestamp: '2024-04-28 14:32:11',
    explanationMethods: ['saliency', 'neighbors', 'influence'],
  },
  {
    id: 'XAI-2024-0002',
    assetId: 'vid_56f4b3c1',
    assetType: 'video',
    model: 'v3.2.1',
    prediction: 'Flagged',
    confidence: 0.34,
    timestamp: '2024-04-28 13:45:22',
    explanationMethods: ['saliency', 'gradient'],
  },
  {
    id: 'XAI-2024-0003',
    assetId: 'img_65f5c4d2',
    assetType: 'image',
    model: 'v3.2.0',
    prediction: 'Pending',
    confidence: 0.51,
    timestamp: '2024-04-28 12:18:05',
    explanationMethods: ['saliency', 'neighbors'],
  },
];

const explanationMethodLabels: Record<string, string> = {
  saliency: 'Saliency Maps',
  gradient: 'Gradient Analysis',
  neighbors: 'Similar Cases',
  influence: 'Influence Functions',
};

export default function XAIViewerPage() {
  const [selectedRecord, setSelectedRecord] = useState<XAIRecord>(DEMO_RECORDS[0]);
  const [activeTab, setActiveTab] = useState<'saliency' | 'gradient' | 'neighbors' | 'influence'>('saliency');
  const [searchTerm, setSearchTerm] = useState('');
  const [isContextPanelOpen, setIsContextPanelOpen] = useState(false);
  const [serviceStatus, setServiceStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    let cancelled = false;

    const checkBackend = async () => {
      try {
        const token = localStorage.getItem('sentinel-access-token') || '';
        if (!token) {
          if (!cancelled) setServiceStatus('offline');
          return;
        }

        const response = await fetch('/api/xai/health/drift', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!cancelled) {
          setServiceStatus(response.ok ? 'online' : 'offline');
        }
      } catch {
        if (!cancelled) {
          setServiceStatus('offline');
        }
      }
    };

    checkBackend();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredRecords = useMemo(
    () =>
      DEMO_RECORDS.filter(
        (record) =>
          searchTerm === '' ||
          record.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          record.assetId.toLowerCase().includes(searchTerm.toLowerCase()),
      ),
    [searchTerm],
  );

  const tabs = selectedRecord.explanationMethods as Array<'saliency' | 'gradient' | 'neighbors' | 'influence'>;
  const validTab = tabs.includes(activeTab) ? activeTab : tabs[0];

  return (
    <MainLayout
      breadcrumb={[{ label: 'XAI Viewer' }]}
      contextPanelTitle={selectedRecord ? `${selectedRecord.assetId}` : 'Asset Details'}
      contextPanelContent={
        selectedRecord && (
          <div className="space-y-6">
            {/* Asset Header */}
            <div className="space-y-3">
              <div>
                <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold mb-1">
                  Record ID
                </p>
                <p className="text-sm font-mono text-accent">{selectedRecord.id}</p>
              </div>

              <div>
                <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold mb-1">
                  Asset ID
                </p>
                <p className="text-sm font-mono text-text-secondary">{selectedRecord.assetId}</p>
              </div>

              <div>
                <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold mb-1">
                  Type
                </p>
                <span className="px-2 py-1 rounded text-xs font-semibold bg-surface-tertiary text-text-secondary">
                  {selectedRecord.assetType.toUpperCase()}
                </span>
              </div>
            </div>

            {/* Prediction */}
            <div className="border-t border-border-subtle pt-4 space-y-3">
              <div>
                <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold mb-1">
                  Prediction
                </p>
                <p className="text-sm text-text-primary font-semibold">{selectedRecord.prediction}</p>
              </div>

              <div>
                <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold mb-2">
                  Confidence
                </p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">
                      {(selectedRecord.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full h-3 bg-surface-tertiary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-accent"
                      style={{ width: `${selectedRecord.confidence * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              <div>
                <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold mb-1">
                  Model
                </p>
                <p className="text-sm text-text-secondary">{selectedRecord.model}</p>
              </div>
            </div>

            {/* Explanation Methods */}
            <div className="border-t border-border-subtle pt-4">
              <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold mb-3">
                Explanations Available
              </p>
              <div className="space-y-2">
                {selectedRecord.explanationMethods.map((method) => (
                  <button
                    key={method}
                    onClick={() => setActiveTab(method)}
                    className={`w-full text-left px-3 py-2 rounded text-xs font-semibold transition-colors duration-fast ${
                      validTab === method
                        ? 'bg-accent text-text-primary'
                        : 'bg-surface-tertiary text-text-secondary hover:bg-surface-elevated'
                    }`}
                  >
                    {explanationMethodLabels[method]}
                  </button>
                ))}
              </div>
            </div>

            {/* Metadata */}
            <div className="border-t border-border-subtle pt-4">
              <p className="text-xs text-text-tertiary font-mono">{selectedRecord.timestamp}</p>
            </div>

            <div className="border-t border-border-subtle pt-4 space-y-2">
              <Button size="sm" className="w-full" disabled={serviceStatus !== 'online'}>
                Export Explanation
              </Button>
              <Button variant="secondary" size="sm" className="w-full" disabled={serviceStatus !== 'online'}>
                Download Assets
              </Button>
              {serviceStatus !== 'online' && (
                <p className="text-xs text-text-tertiary">
                  These actions stay disabled until the XAI record API is available.
                </p>
              )}
            </div>
          </div>
        )
      }
      contextPanelActions={null}
      isContextPanelOpen={isContextPanelOpen}
      onContextPanelClose={() => setIsContextPanelOpen(false)}
    >
      {/* Main Content */}
      <div className="space-y-6">
        {/* Page Header */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold text-text-primary">XAI Viewer</h1>
          <p className="text-lg text-text-secondary">
            Explore model explanations, saliency maps, and decision drivers
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
          <Input
            label="Search Records"
            placeholder="Record ID, Asset ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <div className="rounded-xl border border-border-default bg-surface-secondary px-4 py-3">
            <p className="text-xs uppercase tracking-[0.18em] text-text-tertiary">Backend status</p>
            <p className="mt-2 text-sm text-text-primary">
              {serviceStatus === 'checking'
                ? 'Checking XAI service health...'
                : serviceStatus === 'online'
                  ? 'Connected to backend XAI health endpoints.'
                  : 'This page is currently showing demo records only.'}
            </p>
          </div>
        </div>

        {/* Layout: List on Left, Viewer on Right */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Record List */}
          <div className="lg:col-span-1">
            <div className="space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto">
              {filteredRecords.map((record) => (
                <button
                  key={record.id}
                  onClick={() => {
                    setSelectedRecord(record);
                    setIsContextPanelOpen(true);
                  }}
                  className={`w-full text-left p-3 rounded-xl border transition-colors duration-fast ${
                    selectedRecord.id === record.id
                      ? 'bg-surface-elevated border-accent shadow-glow'
                      : 'bg-surface-secondary border-border-default hover:bg-surface-tertiary'
                  }`}
                >
                  <p className="text-xs font-mono text-accent mb-1">{record.id}</p>
                  <p className="text-xs text-text-secondary truncate">{record.assetId}</p>
                  <p className="text-xs text-text-tertiary mt-1">
                    {record.prediction} • {(record.confidence * 100).toFixed(0)}%
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Viewer */}
          <div className="lg:col-span-3">
            <div className="space-y-6">
              {/* Asset Preview Area */}
              <div className="aspect-video rounded-xl border border-border-default bg-surface-secondary flex items-center justify-center overflow-hidden">
                <div className="text-center space-y-4">
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-accent/10 text-accent">
                    <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="M4 7.5h16M7.5 4v7m9-7v7M5 12.5h14v7H5z" />
                    </svg>
                  </div>
                  <p className="text-text-secondary">{selectedRecord.assetId}</p>
                  <p className="text-xs text-text-tertiary mt-2">
                    {selectedRecord.assetType.toUpperCase()} Asset
                  </p>
                </div>
              </div>

              {/* Explanation Tabs */}
              <div className="space-y-4">
                {/* Tab Buttons */}
                <div className="flex gap-2 overflow-x-auto">
                  {tabs.map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap transition-colors duration-fast ${
                        validTab === tab
                          ? 'bg-accent text-text-primary'
                          : 'bg-surface-secondary text-text-secondary hover:bg-surface-tertiary'
                      }`}
                    >
                      {explanationMethodLabels[tab]}
                    </button>
                  ))}
                </div>

                {/* Tab Content */}
                <div className="p-6 rounded-xl border border-border-default bg-surface-secondary space-y-4">
                  {validTab === 'saliency' && (
                    <div className="space-y-3">
                      <h3 className="text-sm font-semibold text-text-primary">Saliency Maps</h3>
                      <p className="text-xs text-text-secondary">
                        Highlights regions of the input that most influence the model&apos;s decision. Warmer colors
                        indicate higher importance.
                      </p>
                      <div className="aspect-video rounded-xl bg-surface-tertiary flex items-center justify-center">
                        <p className="text-text-tertiary text-sm">Saliency visualization area</p>
                      </div>
                      <div className="text-xs text-text-tertiary">
                        <p>Method: GradCAM (Selvaraju et al., 2016)</p>
                        <p>Resolution: Original asset dimensions</p>
                      </div>
                    </div>
                  )}

                  {validTab === 'gradient' && (
                    <div className="space-y-3">
                      <h3 className="text-sm font-semibold text-text-primary">Gradient Analysis</h3>
                      <p className="text-xs text-text-secondary">
                        Shows the direction and magnitude of gradients flowing through the network at each layer.
                        Identifies which features are most relevant for classification.
                      </p>
                      <div className="aspect-video rounded-xl bg-surface-tertiary flex items-center justify-center">
                        <p className="text-text-tertiary text-sm">Gradient visualization area</p>
                      </div>
                      <div className="text-xs text-text-tertiary">
                        <p>Method: Input Gradient Attribution</p>
                        <p>Layers analyzed: 5</p>
                      </div>
                    </div>
                  )}

                  {validTab === 'neighbors' && (
                    <div className="space-y-3">
                      <h3 className="text-sm font-semibold text-text-primary">Similar Cases</h3>
                      <p className="text-xs text-text-secondary">
                        Displays similar examples from the training data that informed the model&apos;s decision.
                      </p>

                      <div className="grid grid-cols-3 gap-3">
                        {[1, 2, 3].map((i) => (
                          <div key={i} className="space-y-2">
                            <div className="aspect-square rounded-xl bg-surface-tertiary flex items-center justify-center">
                              <span className={`text-sm font-semibold ${i % 2 === 0 ? 'text-success' : 'text-danger'}`}>
                                {i % 2 === 0 ? 'Match' : 'Mismatch'}
                              </span>
                            </div>
                            <div className="text-xs">
                              <p className="text-text-secondary">Similarity: {(90 - i * 5)}%</p>
                              <p className="text-text-tertiary">Training ID: TRAIN-{1000 + i}</p>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="text-xs text-text-tertiary">
                        <p>Method: Nearest Neighbor (Euclidean Distance)</p>
                        <p>Training set: 50K images</p>
                      </div>
                    </div>
                  )}

                  {validTab === 'influence' && (
                    <div className="space-y-3">
                      <h3 className="text-sm font-semibold text-text-primary">Influence Functions</h3>
                      <p className="text-xs text-text-secondary">
                        Identifies which training examples had the most influence on this prediction. Useful for
                        understanding data dependencies.
                      </p>

                      <div className="space-y-2">
                        {[
                          { id: 'TRAIN-0042', influence: 0.87, label: 'High Influence' },
                          { id: 'TRAIN-0156', influence: 0.64, label: 'Medium Influence' },
                          { id: 'TRAIN-0203', influence: 0.41, label: 'Moderate Influence' },
                        ].map((item) => (
                          <div key={item.id} className="space-y-1">
                            <div className="flex justify-between items-center text-xs">
                              <span className="text-text-secondary">{item.id}</span>
                              <span className="text-text-tertiary">{item.label}</span>
                            </div>
                            <div className="w-full h-2 bg-surface-tertiary rounded-full overflow-hidden">
                              <div
                                className="h-full bg-accent"
                                style={{ width: `${item.influence * 100}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="text-xs text-text-tertiary">
                        <p>Method: Influence Functions (Koh & Liang, 2017)</p>
                        <p>Top influencers: 3</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Export Section */}
              <div className="p-4 rounded-xl border border-border-default bg-surface-secondary">
                <p className="text-xs text-text-secondary uppercase letter-spacing-wide font-semibold mb-3">
                  Export Formats
                </p>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" disabled={serviceStatus !== 'online'}>
                    PDF
                  </Button>
                  <Button variant="secondary" size="sm" disabled={serviceStatus !== 'online'}>
                    JSON
                  </Button>
                  <Button variant="secondary" size="sm" disabled={serviceStatus !== 'online'}>
                    PNG
                  </Button>
                </div>
                {serviceStatus !== 'online' && (
                  <p className="mt-3 text-xs text-text-tertiary">
                    Export is disabled because this page is not yet backed by a record retrieval API.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
