'use client';

import React from 'react';

type StatusType = 'approved' | 'rejected' | 'pending' | 'flagged' | 'anchored' | 'reviewing';

interface StatusChipProps {
  status: StatusType;
  size?: 'sm' | 'md';
  className?: string;
}

const statusConfig: Record<
  StatusType,
  { icon: string; label: string; colorVar: string; bgColorVar: string }
> = {
  approved: {
    icon: '✓',
    label: 'APPROVED',
    colorVar: 'var(--color-success)',
    bgColorVar: 'var(--color-success-bg)',
  },
  rejected: {
    icon: '✗',
    label: 'REJECTED',
    colorVar: 'var(--color-danger)',
    bgColorVar: 'var(--color-danger-bg)',
  },
  pending: {
    icon: '⏳',
    label: 'PENDING',
    colorVar: 'var(--color-warning)',
    bgColorVar: 'var(--color-warning-bg)',
  },
  flagged: {
    icon: '⚑',
    label: 'FLAGGED',
    colorVar: 'var(--color-danger)',
    bgColorVar: 'var(--color-danger-bg)',
  },
  anchored: {
    icon: '⛓',
    label: 'ANCHORED',
    colorVar: 'var(--color-accent)',
    bgColorVar: 'var(--color-accent-muted)',
  },
  reviewing: {
    icon: '◌',
    label: 'REVIEWING',
    colorVar: 'var(--color-neutral)',
    bgColorVar: 'var(--color-neutral-bg)',
  },
};

/**
 * StatusChip - Sentry-inspired badge for decision states
 * 
 * - Always uses icon + text (never color-only)
 * - Uppercase label with 0.06em letter-spacing
 * - Semantic colors mapped to status type
 */
export function StatusChip({
  status,
  size = 'md',
  className = '',
}: StatusChipProps) {
  const config = statusConfig[status];

  const sizeClasses = {
    sm: 'px-2 py-1 text-2xs gap-1',
    md: 'px-2 py-1 text-xs gap-1.5',
  };

  return (
    <div
      className={`inline-flex items-center font-semibold rounded-sm ${sizeClasses[size]} ${className}`}
      style={{
        backgroundColor: config.bgColorVar,
        color: config.colorVar,
        letterSpacing: '0.06em',
      }}
    >
      <span className="text-sm leading-none">{config.icon}</span>
      <span className="uppercase font-semibold leading-tight">{config.label}</span>
    </div>
  );
}

export default StatusChip;
