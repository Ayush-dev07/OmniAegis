export type ViewKey =
  | 'overview'
  | 'monitoring'
  | 'threat-map'
  | 'health'
  | 'api';

export type ThreatStatus = 'Queued' | 'Reviewing' | 'Contained' | 'Escalated';

export type RiskLevel = 'Low' | 'Medium' | 'High' | 'Critical';

export interface ThreatItem {
  id: string;
  title: string;
  assetName: string;
  createdAt: string;
  source: string;
  region: string;
  timestamp: string;
  riskScore: number;
  riskLevel: RiskLevel;
  status: ThreatStatus;
  explainability: string;
  similarity: number;
  sourcePreview: string;
  flaggedPreview: string;
  category: string;
}

export interface FeedEntry {
  id: string;
  timestamp: string;
  message: string;
  level: 'info' | 'warn' | 'critical' | 'success';
}

export interface KpiStat {
  label: string;
  value: string;
  delta: string;
  trend: 'up' | 'down';
  icon: string;
}

export interface TrendPoint {
  time: string;
  attempts: number;
  blocked: number;
}

export interface RegionalDatum {
  name: string;
  value: number;
  severity: 'Low' | 'Medium' | 'High' | 'Critical';
}

export interface HealthMetric {
  label: string;
  value: string;
  status: 'Healthy' | 'Warning' | 'Degraded';
}

export interface ApiEndpointMetric {
  method: string;
  endpoint: string;
  latency: string;
  status: '200' | '201' | '429' | '503';
}