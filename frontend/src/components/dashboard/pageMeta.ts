import type { ViewKey } from '@/types/dashboard';

export const pageCopy: Record<ViewKey, { title: string; subtitle: string }> = {
  overview: {
    title: 'Dashboard Overview',
    subtitle: 'A compact operational view of SentinelAgent enforcement, health, and coverage.',
  },
  monitoring: {
    title: 'Active Monitoring Queue',
    subtitle: 'Human-in-the-loop triage for potential intellectual property and policy violations.',
  },
  'threat-map': {
    title: 'Threat Map',
    subtitle: 'Regional concentration of unauthorized source activity and repeated enforcement patterns.',
  },
  health: {
    title: 'System Health',
    subtitle: 'Audit logs and platform telemetry for safety, reliability, and compliance.',
  },
  api: {
    title: 'API Configuration',
    subtitle: 'Operational endpoints and integration health for policy enforcement workflows.',
  },
};
