'use client';

import React, { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

/**
 * Input component following OmniAegis design system
 */
export function Input({
  label,
  error,
  helperText,
  id,
  className = '',
  ...props
}: InputProps) {
  return (
    <div className="w-full flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={id}
          className="text-sm font-medium text-text-primary"
        >
          {label}
        </label>
      )}
      <input
        id={id}
        className={`px-3 py-2.5 rounded-lg text-sm font-medium border transition-all duration-fast focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent placeholder:text-text-tertiary ${
          error
            ? 'border-danger/40 bg-danger-bg text-text-primary'
            : 'border-border-default bg-surface-primary text-text-primary hover:border-border-strong focus-visible:border-accent'
        } ${className}`}
        {...props}
      />
      {error && <span className="text-xs text-danger">{error}</span>}
      {helperText && !error && (
        <span className="text-xs text-text-secondary">{helperText}</span>
      )}
    </div>
  );
}

export default Input;
