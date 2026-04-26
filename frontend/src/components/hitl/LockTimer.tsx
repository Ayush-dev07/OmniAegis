import { useEffect, useState } from 'react';
import { useHITLReview } from '@/context/HITLReviewContext';
import { GlassCard } from '@/components/common/GlassCard';

interface LockTimerProps {
  lockExpiresAt: number | null;
  warningThresholdSeconds?: number;
}

export function LockTimer({ lockExpiresAt, warningThresholdSeconds = 300 }: LockTimerProps) {
  const { setAssignmentLockRemaining } = useHITLReview();
  const [secondsRemaining, setSecondsRemaining] = useState(0);
  const [isWarning, setIsWarning] = useState(false);

  useEffect(() => {
    if (!lockExpiresAt) {
      setSecondsRemaining(0);
      setIsWarning(false);
      return;
    }

    const updateTimer = () => {
      const now = Date.now();
      const remaining = Math.max(0, Math.floor((lockExpiresAt - now) / 1000));

      setSecondsRemaining(remaining);
      setIsWarning(remaining <= warningThresholdSeconds && remaining > 0);
      setAssignmentLockRemaining(remaining);

      if (remaining > 0) {
        const nextUpdate = setTimeout(updateTimer, 1000);
        return () => clearTimeout(nextUpdate);
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [lockExpiresAt, warningThresholdSeconds, setAssignmentLockRemaining]);

  if (!lockExpiresAt || secondsRemaining === 0) {
    return null;
  }

  const minutes = Math.floor(secondsRemaining / 60);
  const seconds = secondsRemaining % 60;

  return (
    <GlassCard
      className={`p-3 border-l-4 ${
        isWarning ? 'border-l-amber-400 bg-amber-400/5' : 'border-l-cyan-400 bg-cyan-400/5'
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-300">
          Assignment Lock Expires In
        </span>
        <span
          className={`font-mono text-sm font-bold ${
            isWarning ? 'text-amber-400' : 'text-cyan-300'
          }`}
        >
          {minutes}:{seconds.toString().padStart(2, '0')}
        </span>
      </div>
      {isWarning && (
        <div className="mt-2 text-xs text-amber-300">
          ⚠️ Lock expiring soon. Complete review or escalate.
        </div>
      )}
    </GlassCard>
  );
}
