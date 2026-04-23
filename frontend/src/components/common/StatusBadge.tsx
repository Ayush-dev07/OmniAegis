import type { ReactNode } from 'react';
import { themeTokens, toneClasses, type Tone } from '@/theme/theme';

interface StatusBadgeProps {
  label: string;
  tone?: Tone;
  className?: string;
  icon?: ReactNode;
  uppercase?: boolean;
}

export function StatusBadge({ label, tone = 'neutral', className = '', icon, uppercase = false }: StatusBadgeProps) {
  return (
    <span
      className={[
        themeTokens.radius.badge,
        themeTokens.badge.base,
        toneClasses[tone],
        uppercase ? 'uppercase tracking-[0.25em]' : '',
        className,
      ].join(' ')}
    >
      {icon}
      {label}
    </span>
  );
}
