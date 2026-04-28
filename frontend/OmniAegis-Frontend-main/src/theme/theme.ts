export const colors = {
  background: '#0A0A0A', // deep obsidian
  surface: 'rgba(255,255,255,0.02)',
  glassBorder: 'rgba(255,255,255,0.06)',
  accent: '#00E6A8', // cyber teal (used as accent for focus/links) - chosen for readability on obsidian
  danger: '#FF6B6B',
  success: '#4ADE80',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 40,
};

export const theme = {
  colors,
  spacing,
};

export type Theme = typeof theme;
