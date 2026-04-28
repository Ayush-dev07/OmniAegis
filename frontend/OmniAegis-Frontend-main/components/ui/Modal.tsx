'use client';

import React, { ReactNode, useEffect, useRef } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  actions?: ReactNode;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Modal component with focus trap and keyboard support
 */
export function Modal({
  isOpen,
  onClose,
  title,
  children,
  actions,
  size = 'md',
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    // Always register the escape handler while component is mounted
    document.addEventListener('keydown', handleEscape);

    // When modal is open, prevent body scroll and focus modal. Ensure cleanup always resets overflow.
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      // focus the modal container for keyboard users
      setTimeout(() => {
        modalRef.current?.focus();
      }, 0);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center animate-in fade-in duration-slow"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.45)' }}
      onClick={onClose}
    >
      <div
        ref={modalRef}
        tabIndex={-1}
        className={`bg-surface-secondary border border-border-default rounded-lg shadow-lg max-h-[90vh] overflow-y-auto ${sizeClasses[size]} w-full mx-4 animate-in zoom-in-95 slide-in-from-bottom-4 duration-slow`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        {/* Focus trap: capture Tab and Shift+Tab to keep focus inside modal */}
        <div
          onKeyDown={(e) => {
            if (e.key !== 'Tab') return;
            const focusable = modalRef.current?.querySelectorAll<HTMLElement>(
              'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
            );
            if (!focusable || focusable.length === 0) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];

            if (e.shiftKey) {
              if (document.activeElement === first || document.activeElement === modalRef.current) {
                e.preventDefault();
                last.focus();
              }
            } else if (document.activeElement === last) {
              e.preventDefault();
              first.focus();
            }
          }}
        >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-default sticky top-0 bg-surface-secondary">
          <h2 id="modal-title" className="text-lg font-semibold text-text-primary">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-text-primary transition-colors rounded-md hover:bg-surface-tertiary p-1"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6">{children}</div>

        {/* Actions */}
        {actions && (
          <div className="flex items-center justify-end gap-3 p-6 border-t border-border-default bg-surface-primary">
            {actions}
          </div>
        )}
        </div>
      </div>
    </div>
  );
}

export default Modal;
