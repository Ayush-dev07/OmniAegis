'use client';

import React, { useEffect } from 'react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastProps {
  message: string;
  type?: ToastType;
  duration?: number;
  onClose?: () => void;
}

const typeConfig: Record<
  ToastType,
  { icon: string; colorVar: string; bgColorVar: string }
> = {
  success: {
    icon: '✓',
    colorVar: 'var(--color-success)',
    bgColorVar: 'var(--color-success-bg)',
  },
  error: {
    icon: '✗',
    colorVar: 'var(--color-danger)',
    bgColorVar: 'var(--color-danger-bg)',
  },
  warning: {
    icon: '⚠',
    colorVar: 'var(--color-warning)',
    bgColorVar: 'var(--color-warning-bg)',
  },
  info: {
    icon: 'ℹ',
    colorVar: 'var(--color-accent)',
    bgColorVar: 'var(--color-accent-muted)',
  },
};

/**
 * Toast notification component
 * Appears bottom-right, auto-dismisses after duration
 */
export function Toast({
  message,
  type = 'info',
  duration = 4000,
  onClose,
}: ToastProps) {
  const config = typeConfig[type];

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => onClose?.(), duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  return (
    <div
      className="flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg animate-in fade-in slide-in-from-bottom-4 duration-normal"
      style={{
        backgroundColor: config.bgColorVar,
        color: config.colorVar,
        border: `1px solid ${config.colorVar}`,
      }}
    >
      <span className="text-lg leading-none">{config.icon}</span>
      <span className="text-sm font-medium flex-1">{message}</span>
      <button
        onClick={onClose}
        className="text-lg leading-none opacity-50 hover:opacity-100 transition-opacity"
      >
        ✕
      </button>
    </div>
  );
}

export default Toast;
