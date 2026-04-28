'use client';

import React, { ReactNode, useEffect, useRef } from 'react';

interface ContextPanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  actions?: ReactNode;
}

/**
 * Context Panel - 380px right slide-in overlay
 * 
 * - Never a route change
 * - Always overlays main content
 * - Dismissable with Escape, [×] button, or backdrop click
 * - Fixed width, scrollable content
 */
export function ContextPanel({
  isOpen,
  onClose,
  title,
  children,
  actions,
}: ContextPanelProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => panelRef.current?.focus(), 0);
    }
  }, [isOpen]);

  return (
    <>
      {/* Backdrop */}
      {isOpen && <div className="fixed inset-0 bg-black/12 z-40 animate-in fade-in duration-normal" onClick={onClose} />}

      {/* Panel */}
      <aside
        ref={panelRef}
        tabIndex={-1}
        onKeyDown={(e) => {
          if (e.key !== 'Tab') return;
          const focusable = panelRef.current?.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
          );
          if (!focusable || focusable.length === 0) return;
          const first = focusable[0];
          const last = focusable[focusable.length - 1];
          if (e.shiftKey) {
            if (document.activeElement === first) {
              e.preventDefault();
              last.focus();
            }
          } else {
            if (document.activeElement === last) {
              e.preventDefault();
              first.focus();
            }
          }
        }}
        className={`fixed right-0 top-14 h-[calc(100vh-56px)] w-96 bg-surface-secondary border-l border-border-default shadow-lg z-50 transition-transform duration-normal ${
          isOpen ? 'translate-x-0 pointer-events-auto' : 'translate-x-full pointer-events-none'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border-default sticky top-0 bg-surface-secondary">
          <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-text-primary transition-colors rounded-md hover:bg-surface-tertiary p-1"
            aria-label="Close panel"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto h-[calc(100%-56px-64px)] p-6 space-y-4">
          {children}
        </div>

        {/* Actions Footer */}
        {actions && (
          <div className="flex items-center justify-end gap-3 p-4 border-t border-border-default bg-surface-primary sticky bottom-0">
            {actions}
          </div>
        )}
      </aside>
    </>
  );
}

export default ContextPanel;
