import { AnimatePresence, motion } from 'framer-motion';
import { X, ShieldCheck, Ban, Gavel, AlertCircle } from 'lucide-react';
import type { ThreatItem } from '@/types/dashboard';
import { GlassCard } from '@/components/common/GlassCard';
import { StatusBadge } from '@/components/common/StatusBadge';
import { riskToneMap } from '@/theme/theme';

interface ActionCardProps {
  threat: ThreatItem | null;
  onClose: () => void;
  onApprove: (threat: ThreatItem) => void;
  onTakedown: (threat: ThreatItem) => void;
  onEscalate: (threat: ThreatItem) => void;
}

export function ActionCard({ threat, onClose, onApprove, onTakedown, onEscalate }: ActionCardProps) {
  return (
    <AnimatePresence>
      {threat ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[70] flex items-end justify-center bg-slate-950/75 p-3 backdrop-blur-sm lg:items-center"
          onClick={onClose}
        >
          <motion.div
            initial={{ y: 48, opacity: 0, scale: 0.98 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: 32, opacity: 0, scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 260, damping: 28 }}
            className="w-full max-w-5xl"
            onClick={(event) => event.stopPropagation()}
          >
            <GlassCard className="overflow-hidden">
              <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.35em] text-cyan-300/80">Action Card</p>
                  <h3 className="mt-1 text-lg font-semibold text-slate-50">{threat.title}</h3>
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-xl border border-white/10 bg-white/5 p-2 text-slate-300"
                  aria-label="Close threat details"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="grid gap-0 lg:grid-cols-[1.1fr_0.9fr]">
                <div className="border-b border-white/10 p-5 lg:border-b-0 lg:border-r">
                  <p className="text-sm text-slate-400">Media Preview</p>
                  <div className="mt-3 grid gap-4 sm:grid-cols-2">
                    <figure className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900">
                      <img src={threat.sourcePreview} alt="Source media preview" className="h-56 w-full object-cover" />
                      <figcaption className="border-t border-white/10 px-3 py-2 text-xs text-slate-400">Source</figcaption>
                    </figure>
                    <figure className="overflow-hidden rounded-2xl border border-rose-400/20 bg-slate-900">
                      <img src={threat.flaggedPreview} alt="Flagged media preview" className="h-56 w-full object-cover" />
                      <figcaption className="border-t border-rose-400/20 px-3 py-2 text-xs text-rose-300">Flagged</figcaption>
                    </figure>
                  </div>

                  <div className="mt-5 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Explainability Trace</p>
                      <p className="mt-2 text-sm leading-6 text-slate-200">{threat.explainability}</p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Metadata</p>
                      <div className="mt-2 space-y-2 text-sm text-slate-300">
                        <p>ID: {threat.id}</p>
                        <p>Asset: {threat.assetName}</p>
                        <p>Source: {threat.source}</p>
                        <p>Region: {threat.region}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-5">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm text-slate-400">Risk score</p>
                      <div className="mt-2 flex items-center gap-3">
                        <StatusBadge label={threat.riskLevel} tone={riskToneMap[threat.riskLevel]} />
                        <span className="text-4xl font-semibold text-slate-50">{threat.riskScore}</span>
                      </div>
                    </div>
                    <div className="rounded-2xl border border-amber-400/20 bg-amber-400/10 p-3 text-amber-300">
                      <AlertCircle className="h-6 w-6" />
                    </div>
                  </div>

                  <div className="mt-5 rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                    <div className="flex items-center justify-between text-sm text-slate-300">
                      <span>Structural similarity</span>
                      <span>{threat.similarity}%</span>
                    </div>
                    <div className="mt-3 h-3 overflow-hidden rounded-full bg-white/10">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-violet-400 to-rose-400"
                        style={{ width: `${threat.similarity}%` }}
                      />
                    </div>
                    <p className="mt-3 text-xs leading-6 text-slate-400">
                      The model aligns visual hierarchy, asset fingerprinting, and source provenance to determine enforcement priority.
                    </p>
                  </div>

                  <div className="mt-5 grid gap-3">
                    <button
                      type="button"
                      onClick={() => onApprove(threat)}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl bg-emerald-400 px-4 py-3 text-sm font-medium text-slate-950 transition hover:bg-emerald-300"
                    >
                      <ShieldCheck className="h-4 w-4" />
                      Approve / Whitelist
                    </button>
                    <button
                      type="button"
                      onClick={() => onTakedown(threat)}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm font-medium text-rose-200 transition hover:bg-rose-400/15"
                    >
                      <Ban className="h-4 w-4" />
                      Issue Takedown
                    </button>
                    <button
                      type="button"
                      onClick={() => onEscalate(threat)}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-slate-100 transition hover:bg-white/10"
                    >
                      <Gavel className="h-4 w-4" />
                      Escalate to Legal
                    </button>
                  </div>
                </div>
              </div>
            </GlassCard>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}