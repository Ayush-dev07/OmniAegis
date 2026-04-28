'use client';

import React, { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: ReactNode;
  isLoading?: boolean;
  children: ReactNode;
}

/**
 * Button component following OmniAegis design system
 * 
 * Variants:
 * - primary: Accent color, main CTA
 * - secondary: Border-based, secondary action
 * - danger: Red color, destructive action
 * - ghost: Transparent with border on hover
 */
export function Button({
  variant = 'primary',
  size = 'md',
  icon,
  isLoading = false,
  className = '',
  disabled = false,
  ...props
}: ButtonProps) {
  const baseClasses =
    'inline-flex items-center justify-center gap-2 font-semibold rounded-lg transition-all duration-fast font-feature-settings text-sm disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2';

  const variantClasses: Record<ButtonVariant, string> = {
    primary:
      'bg-accent text-text-inverse hover:bg-accent-hover focus-visible:outline-accent shadow-sm hover:shadow-md',
    secondary:
      'bg-surface-tertiary text-text-primary hover:bg-surface-elevated focus-visible:outline-accent',
    danger:
      'bg-danger-bg text-danger hover:bg-danger/20 focus-visible:outline-danger',
    ghost:
      'bg-transparent text-text-primary hover:bg-surface-tertiary focus-visible:outline-accent',
  };

  const sizeClasses: Record<ButtonSize, string> = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {icon && <span className="text-base">{icon}</span>}
      {isLoading && (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {props.children}
    </button>
  );
}

export default Button;
