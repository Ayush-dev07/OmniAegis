import { useCallback, useState } from 'react';
import { useHITLReview, type HITLReviewDecision } from '@/context/HITLReviewContext';
import { GlassCard } from '@/components/common/GlassCard';

type DecisionType = 'INFRINGING' | 'NOT_INFRINGING' | 'ESCALATE';
type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';

interface DecisionPanelProps {
  onSubmit?: (decision: HITLReviewDecision) => void | Promise<void>;
  isLoading?: boolean;
}

export function DecisionPanel({ onSubmit, isLoading = false }: DecisionPanelProps) {
  const { state, setDecision, resetDecision } = useHITLReview();
  const [selectedDecision, setSelectedDecision] = useState<DecisionType | null>(null);
  const [selectedConfidence, setSelectedConfidence] = useState<ConfidenceLevel>('MEDIUM');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleDecisionClick = (decision: DecisionType) => {
    setSelectedDecision(decision);
  };

  const handleConfidenceChange = (confidence: ConfidenceLevel) => {
    setSelectedConfidence(confidence);
  };

  const handleSubmit = useCallback(async () => {
    if (!selectedDecision || !state.currentItem) {
      return;
    }

    const decision: HITLReviewDecision = {
      item_id: state.currentItem.item_id,
      decision: selectedDecision,
      confidence: selectedConfidence,
      notes: notes || undefined,
      decided_at_ms: Date.now(),
    };

    setIsSubmitting(true);
    try {
      setDecision(decision);
      if (onSubmit) {
        await onSubmit(decision);
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [selectedDecision, selectedConfidence, notes, state.currentItem, setDecision, onSubmit]);

  const handleReset = () => {
    setSelectedDecision(null);
    setSelectedConfidence('MEDIUM');
    setNotes('');
    resetDecision();
  };

  const decisionButtons: Array<{
    label: string;
    value: DecisionType;
    color: string;
    bgColor: string;
  }> = [
    {
      label: 'NOT INFRINGING',
      value: 'NOT_INFRINGING',
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-400/10 border-emerald-400/30 hover:bg-emerald-400/20',
    },
    {
      label: 'INFRINGING',
      value: 'INFRINGING',
      color: 'text-rose-400',
      bgColor: 'bg-rose-400/10 border-rose-400/30 hover:bg-rose-400/20',
    },
    {
      label: 'ESCALATE',
      value: 'ESCALATE',
      color: 'text-amber-400',
      bgColor: 'bg-amber-400/10 border-amber-400/30 hover:bg-amber-400/20',
    },
  ];

  return (
    <GlassCard className="p-5 flex flex-col gap-4">
      <div>
        <h3 className="text-sm font-semibold text-cyan-400 mb-3">Decision</h3>
        <div className="flex flex-col gap-2">
          {decisionButtons.map((btn) => (
            <button
              key={btn.value}
              onClick={() => handleDecisionClick(btn.value)}
              disabled={isSubmitting || isLoading}
              className={`
                px-4 py-2 rounded-lg border transition-colors text-sm font-medium
                ${
                  selectedDecision === btn.value
                    ? `${btn.bgColor} ring-2 ring-offset-1 ring-offset-slate-950`
                    : 'border-white/10 bg-slate-700/30 text-slate-300 hover:bg-slate-700/50'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {selectedDecision && (
        <div>
          <h3 className="text-sm font-semibold text-cyan-400 mb-3">Confidence</h3>
          <div className="flex gap-2">
            {(['LOW', 'MEDIUM', 'HIGH'] as ConfidenceLevel[]).map((level) => (
              <button
                key={level}
                onClick={() => handleConfidenceChange(level)}
                disabled={isSubmitting || isLoading}
                className={`
                  flex-1 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors
                  ${
                    selectedConfidence === level
                      ? 'border-cyan-400 bg-cyan-400/20 text-cyan-300'
                      : 'border-white/10 bg-slate-700/30 text-slate-300 hover:bg-slate-700/50'
                  }
                  disabled:opacity-50 disabled:cursor-not-allowed
                `}
              >
                {level}
              </button>
            ))}
          </div>
        </div>
      )}

      <div>
        <label className="text-xs font-semibold text-slate-300 block mb-2">Notes (Optional)</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          disabled={isSubmitting || isLoading}
          placeholder="Add reasoning or context for your decision..."
          className="w-full px-3 py-2 rounded-lg bg-slate-800/50 border border-white/10 text-slate-200 text-xs placeholder-slate-500 focus:outline-none focus:border-cyan-400/50 focus:ring-1 focus:ring-cyan-400/20 disabled:opacity-50 disabled:cursor-not-allowed resize-none h-16"
        />
      </div>

      <div className="flex gap-2 pt-2">
        <button
          onClick={handleSubmit}
          disabled={!selectedDecision || isSubmitting || isLoading}
          className="flex-1 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-600 text-slate-900 font-semibold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting || isLoading ? 'Submitting...' : 'Submit Decision'}
        </button>
        <button
          onClick={handleReset}
          disabled={isSubmitting || isLoading}
          className="flex-1 px-4 py-2 rounded-lg border border-white/10 bg-slate-700/30 hover:bg-slate-700/50 text-slate-300 font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Reset
        </button>
      </div>
    </GlassCard>
  );
}
