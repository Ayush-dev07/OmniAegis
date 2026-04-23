import type { ReactNode } from 'react';
import { themeTokens } from '@/theme/theme';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
}

export function GlassCard({ children, className = '' }: GlassCardProps) {
  return (
    <div
      className={[
        `${themeTokens.radius.card} overflow-hidden border border-white/15 bg-slate-900/55 backdrop-blur-xl shadow-glass`,
        'ring-1 ring-cyan-400/10',
        className,
      ].join(' ')}
    >
      {children}
    </div>
  );
}