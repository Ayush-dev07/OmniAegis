export const themeTokens = {
  radius: {
    card: 'rounded-2xl',
    control: 'rounded-xl',
    badge: 'rounded-full',
  },
  spacing: {
    cardPadding: 'p-5',
    compactCardPadding: 'p-4',
    sectionGap: 'gap-4',
  },
  badge: {
    base: 'inline-flex items-center gap-1 border px-2.5 py-1 text-xs font-medium',
  },
} as const;

export const toneClasses = {
  neutral: 'border-white/10 bg-white/5 text-slate-300',
  cyan: 'border-cyan-400/20 bg-cyan-400/10 text-cyan-300',
  emerald: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300',
  amber: 'border-amber-400/20 bg-amber-400/10 text-amber-300',
  rose: 'border-rose-400/20 bg-rose-400/10 text-rose-300',
  violet: 'border-violet-400/20 bg-violet-400/10 text-violet-300',
} as const;

export type Tone = keyof typeof toneClasses;

export const riskToneMap = {
  Low: 'emerald',
  Medium: 'cyan',
  High: 'amber',
  Critical: 'rose',
} as const;

export const healthToneMap = {
  Healthy: 'emerald',
  Warning: 'amber',
  Degraded: 'rose',
} as const;
