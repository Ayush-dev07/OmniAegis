'use client';

import React, { useState } from 'react';

interface ConfidenceBadgeProps {
  value: number; // 0.0 - 1.0
  size?: 'sm' | 'md' | 'lg';
  showTooltip?: boolean;
}

/**
 * ConfidenceBadge - CRITICAL COMPONENT
 * 
 * Used on every list row, card, audit record, and HITL task.
 * Always pairs numeric confidence with visual indicator.
 * 
 * - High (≥0.80): Green dot, no animation
 * - Mid (0.20–0.79): Orange dot, no animation
 * - Low (<0.20): Red dot, pulse animation
 */
export function ConfidenceBadge({
  value,
  size = 'md',
  showTooltip = true,
}: ConfidenceBadgeProps) {
  const [showFullPrecision, setShowFullPrecision] = useState(false);

  // Determine color and dot style based on confidence threshold
  let color = 'var(--color-success)';
  let dotStyle = 'solid';

  if (value >= 0.8) {
    color = 'var(--color-success)';
    dotStyle = 'solid'; // Filled dot
  } else if (value >= 0.2) {
    color = 'var(--color-warning)';
    dotStyle = 'half'; // Half dot
  } else {
    color = 'var(--color-danger)';
    dotStyle = 'empty'; // Empty dot + pulse
  }

  // Size mapping
  const sizeClasses = {
    sm: 'text-xs gap-1',
    md: 'text-sm gap-1.5',
    lg: 'text-base gap-2',
  };

  const dotSizeClasses = {
    sm: 'w-1 h-1',
    md: 'w-1.5 h-1.5',
    lg: 'w-2 h-2',
  };

  // Percentage rounded to 1 decimal place by default, 3 with tooltip
  const displayValue = showFullPrecision
    ? (value * 100).toFixed(1)
    : (value * 100).toFixed(1);

  return (
    <div
      className={`flex items-center ${sizeClasses[size]} font-medium`}
      style={{ color }}
      onMouseEnter={() => showTooltip && setShowFullPrecision(true)}
      onMouseLeave={() => setShowFullPrecision(false)}
      title={`Confidence: ${(value * 100).toFixed(2)}%`}
    >
      {/* Dot Indicator */}
      <div className="relative">
        {dotStyle === 'solid' && (
          <div
            className={`${dotSizeClasses[size]} rounded-full`}
            style={{ backgroundColor: color }}
          />
        )}
        {dotStyle === 'half' && (
          <div
            className={`${dotSizeClasses[size]} rounded-full relative overflow-hidden`}
            style={{ backgroundColor: 'transparent', border: `1px solid ${color}` }}
          >
            <div
              className="absolute inset-0"
              style={{
                backgroundColor: color,
                width: '50%',
              }}
            />
          </div>
        )}
        {dotStyle === 'empty' && (
          <div
            className={`${dotSizeClasses[size]} rounded-full border-2 animate-pulse`}
            style={{ borderColor: color }}
          />
        )}
      </div>

      {/* Percentage Text */}
      <span>{displayValue}%</span>
    </div>
  );
}

export default ConfidenceBadge;
