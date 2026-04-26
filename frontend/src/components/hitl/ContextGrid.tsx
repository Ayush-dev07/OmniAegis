import { GlassCard } from '@/components/common/GlassCard';

interface ContextSection {
  label: string;
  value: string | number;
  highlight?: boolean;
}

interface ContextPanelProps {
  title: string;
  sections: ContextSection[];
}

function ContextPanel({ title, sections }: ContextPanelProps) {
  return (
    <GlassCard className="p-4 h-full flex flex-col gap-3">
      <h3 className="text-sm font-semibold text-cyan-400 sticky top-0 bg-gradient-to-b from-slate-900/95 to-slate-900/50 -mx-4 px-4 py-2">
        {title}
      </h3>
      <div className="flex-1 overflow-y-auto space-y-2 pr-2">
        {sections.map((section, idx) => (
          <div key={idx} className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-400">{section.label}</span>
            <span
              className={`text-sm ${
                section.highlight
                  ? 'font-semibold text-cyan-300 bg-cyan-400/10 px-2 py-1 rounded'
                  : 'text-slate-300'
              }`}
            >
              {section.value}
            </span>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

interface ContextGridProps {
  assetId?: string;
  confidence?: number;
  contentType?: string;
  priorityScore?: number;
  submitterId?: string;
  submitterScore?: number;
  rightsNodeIds?: string[];
  metadata?: Record<string, unknown>;
}

export function ContextGrid({
  assetId,
  confidence,
  contentType,
  priorityScore,
  submitterId,
  submitterScore,
  rightsNodeIds = [],
  metadata = {},
}: ContextGridProps) {
  const contextSections: ContextSection[] = [
    { label: 'Asset ID', value: assetId || 'N/A' },
    { label: 'Content Type', value: contentType || 'Unknown', highlight: contentType === 'video' },
    { label: 'Priority Score', value: priorityScore?.toFixed(3) || 'N/A', highlight: (priorityScore ?? 0) > 0.7 },
    { label: 'Initial Confidence', value: confidence ? `${(confidence * 100).toFixed(1)}%` : 'N/A' },
  ];

  const rightsNodeSections: ContextSection[] = [
    { label: 'Rights Nodes Count', value: rightsNodeIds.length },
    ...rightsNodeIds.map((nodeId, idx) => ({
      label: `Node ${idx + 1}`,
      value: nodeId.substring(0, 32) + (nodeId.length > 32 ? '...' : ''),
    })),
  ];

  if (rightsNodeIds.length === 0) {
    rightsNodeSections.push({
      label: 'Status',
      value: 'No rights nodes in context',
    });
  }

  const submitterSections: ContextSection[] = [
    { label: 'Submitter ID', value: submitterId || 'Anonymous' },
    { label: 'Submitter Score', value: submitterScore ? submitterScore.toFixed(3) : 'N/A', highlight: (submitterScore ?? 0) < 0.5 },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 h-full">
      <ContextPanel title="Context" sections={contextSections} />
      <ContextPanel title="Rights Graph Context" sections={rightsNodeSections} />
    </div>
  );
}
