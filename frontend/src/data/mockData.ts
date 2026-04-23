import type {
  ApiEndpointMetric,
  FeedEntry,
  HealthMetric,
  KpiStat,
  RegionalDatum,
  ThreatItem,
  TrendPoint,
} from '@/types/dashboard';

export const kpiStats: KpiStat[] = [
  {
    label: 'Assets Monitored',
    value: '14,382',
    delta: '+12.4% this week',
    trend: 'up',
    icon: 'ShieldCheck',
  },
  {
    label: 'Active Threats Intercepted',
    value: '287',
    delta: '+31 since yesterday',
    trend: 'up',
    icon: 'AlertTriangle',
  },
  {
    label: 'Protection Efficiency',
    value: '98.7%',
    delta: 'Sustained for 21 days',
    trend: 'up',
    icon: 'Sparkles',
  },
];

export const threatTrends: TrendPoint[] = [
  { time: '00:00', attempts: 12, blocked: 11 },
  { time: '03:00', attempts: 19, blocked: 18 },
  { time: '06:00', attempts: 28, blocked: 25 },
  { time: '09:00', attempts: 48, blocked: 44 },
  { time: '12:00', attempts: 37, blocked: 35 },
  { time: '15:00', attempts: 52, blocked: 49 },
  { time: '18:00', attempts: 61, blocked: 58 },
  { time: '21:00', attempts: 39, blocked: 37 },
];

export const regionalDistribution: RegionalDatum[] = [
  { name: 'North America', value: 88, severity: 'High' },
  { name: 'Europe', value: 74, severity: 'Medium' },
  { name: 'South America', value: 32, severity: 'Low' },
  { name: 'Asia Pacific', value: 95, severity: 'Critical' },
  { name: 'Middle East', value: 47, severity: 'Medium' },
  { name: 'Africa', value: 21, severity: 'Low' },
];

export const threatQueue: ThreatItem[] = [
  {
    id: 'SA-1042',
    title: 'Brand-similar product artwork detected',
    assetName: 'Campaign Banner Set A',
    createdAt: '2026-04-23',
    source: 'cdn.thirdparty.net',
    region: 'Asia Pacific',
    timestamp: '2 min ago',
    riskScore: 92,
    riskLevel: 'Critical',
    status: 'Queued',
    explainability: 'Structural similarity 88% with protected asset family; palette, composition, and text layout match.',
    similarity: 88,
    sourcePreview: 'https://images.unsplash.com/photo-1526378722484-bd91ca387e72?auto=format&fit=crop&w=900&q=80',
    flaggedPreview: 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=900&q=80',
    category: 'Visual IP',
  },
  {
    id: 'SA-1043',
    title: 'Unauthorized logo usage in reseller page',
    assetName: 'Partner Brand Kit',
    createdAt: '2026-04-22',
    source: 'mirror.example-corp.com',
    region: 'Europe',
    timestamp: '5 min ago',
    riskScore: 79,
    riskLevel: 'High',
    status: 'Reviewing',
    explainability: 'Logo geometry and wordmark spacing fall within suspicious threshold. The mark is cropped and recolored.',
    similarity: 81,
    sourcePreview: 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80',
    flaggedPreview: 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=900&q=80',
    category: 'Trademark',
  },
  {
    id: 'SA-1044',
    title: 'Credential-gated archive exposed publicly',
    assetName: 'Internal Archive Clip',
    createdAt: '2026-04-21',
    source: 'dropzone.storage',
    region: 'North America',
    timestamp: '9 min ago',
    riskScore: 64,
    riskLevel: 'Medium',
    status: 'Queued',
    explainability: 'Metadata fingerprint aligned with sensitive internal media. Access pattern indicates possible leakage.',
    similarity: 67,
    sourcePreview: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=900&q=80',
    flaggedPreview: 'https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=900&q=80',
    category: 'Leakage',
  },
];

export const liveFeedEntries: FeedEntry[] = [
  { id: 'f1', timestamp: '12:04:11', message: 'Model inference completed for SA-1042', level: 'info' },
  { id: 'f2', timestamp: '12:04:14', message: 'Threat score raised to 92 after visual hash consensus', level: 'critical' },
  { id: 'f3', timestamp: '12:04:19', message: 'Policy engine prepared takedown workflow for review', level: 'warn' },
  { id: 'f4', timestamp: '12:04:26', message: 'Whitelist check passed for asset family on edge cache', level: 'success' },
];

export const healthMetrics: HealthMetric[] = [
  { label: 'Detection Latency', value: '22 ms', status: 'Healthy' },
  { label: 'Queue Backlog', value: '8 items', status: 'Warning' },
  { label: 'Policy Sync', value: 'Complete', status: 'Healthy' },
  { label: 'Inference Workers', value: '12 / 12', status: 'Healthy' },
];

export const apiEndpoints: ApiEndpointMetric[] = [
  { method: 'POST', endpoint: '/v1/assets/scan', latency: '180 ms', status: '200' },
  { method: 'GET', endpoint: '/v1/threats?status=queued', latency: '74 ms', status: '200' },
  { method: 'POST', endpoint: '/v1/actions/escalate', latency: '251 ms', status: '201' },
  { method: 'GET', endpoint: '/v1/health', latency: '96 ms', status: '429' },
];