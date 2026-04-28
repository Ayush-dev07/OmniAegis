import React, { PropsWithChildren } from 'react';
// small helper to avoid adding dependencies
const join = (...parts: Array<string | undefined>) => parts.filter(Boolean).join(' ');
import { theme } from '../../theme/theme';

export interface GlassCardProps {
  className?: string;
  role?: string;
}

const GlassCard: React.FC<PropsWithChildren<GlassCardProps>> = ({ children, className, role }) => {
  return (
    <div
      role={role || 'region'}
      className={join('rounded-lg p-4', 'backdrop-blur-md', 'border', 'shadow-sm', 'overflow-hidden', className)}
      style={{
        background: theme.colors.surface,
        borderColor: theme.colors.glassBorder,
      }}
    >
      {children}
    </div>
  );
};

export default React.memo(GlassCard);
