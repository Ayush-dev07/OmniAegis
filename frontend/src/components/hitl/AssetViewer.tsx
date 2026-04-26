import { useEffect, useRef, useState } from 'react';
import { useHITLReview } from '@/context/HITLReviewContext';
import { GlassCard } from '@/components/common/GlassCard';

interface AssetViewerProps {
  assetUrl?: string;
  assetType?: string;
  saliencyMapUrl?: string;
  fallbackAssetPreview?: string;
}

export function AssetViewer({
  assetUrl,
  assetType = 'image',
  saliencyMapUrl,
  fallbackAssetPreview,
}: AssetViewerProps) {
  const { state, setSaliencyOpacity } = useHITLReview();
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);

  useEffect(() => {
    setImageLoaded(false);
  }, [assetUrl]);

  const displayUrl = assetUrl || fallbackAssetPreview;

  return (
    <GlassCard className="p-4 flex flex-col h-full gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-cyan-400">Primary Evidence</h3>
        {assetType && <span className="text-xs px-2 py-1 rounded bg-slate-700/50 text-slate-300">{assetType}</span>}
      </div>

      <div
        ref={containerRef}
        className="flex-1 relative bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg overflow-hidden min-h-[300px] border border-white/10"
      >
        {assetType === 'image' && displayUrl ? (
          <div className="relative w-full h-full">
            <img
              src={displayUrl}
              alt="Asset under review"
              onLoad={() => setImageLoaded(true)}
              className="w-full h-full object-contain"
            />
            {saliencyMapUrl && (
              <img
                src={saliencyMapUrl}
                alt="XAI Saliency Map"
                className="absolute inset-0 w-full h-full object-contain pointer-events-none transition-opacity duration-200"
                style={{ opacity: state.saliencyOpacity }}
              />
            )}
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-xs text-slate-400">Loading asset...</div>
              </div>
            )}
          </div>
        ) : assetType === 'video' && displayUrl ? (
          <video
            src={displayUrl}
            controls
            className="w-full h-full"
            style={{ maxHeight: '100%', objectFit: 'contain' }}
          />
        ) : assetType === 'audio' && displayUrl ? (
          <div className="w-full h-full flex flex-col items-center justify-center gap-4">
            <div className="text-6xl">🎵</div>
            <audio src={displayUrl} controls className="w-full max-w-xs" />
          </div>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-400 text-sm">
            No asset URL provided
          </div>
        )}
      </div>

      {saliencyMapUrl && (
        <div className="flex flex-col gap-2">
          <label className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300">XAI Saliency Overlay</span>
            <span className="text-xs text-slate-400">{Math.round(state.saliencyOpacity * 100)}%</span>
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={state.saliencyOpacity}
            onChange={(e) => setSaliencyOpacity(parseFloat(e.target.value))}
            className="w-full h-1.5 rounded-full bg-slate-700 appearance-none cursor-pointer accent-cyan-400"
          />
          <div className="flex gap-2 text-xs text-slate-400">
            <button
              onClick={() => setSaliencyOpacity(0)}
              className="px-2 py-1 rounded bg-slate-700/50 hover:bg-slate-700 transition-colors"
            >
              Hide
            </button>
            <button
              onClick={() => setSaliencyOpacity(0.5)}
              className="px-2 py-1 rounded bg-slate-700/50 hover:bg-slate-700 transition-colors"
            >
              50%
            </button>
            <button
              onClick={() => setSaliencyOpacity(1)}
              className="px-2 py-1 rounded bg-slate-700/50 hover:bg-slate-700 transition-colors"
            >
              Full
            </button>
          </div>
        </div>
      )}
    </GlassCard>
  );
}
