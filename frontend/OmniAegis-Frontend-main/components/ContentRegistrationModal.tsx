'use client';

import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from 'react';

type ContentType = 'image' | 'video' | 'audio';

interface ContentRegistrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  userName?: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

const ENDPOINTS: Record<ContentType, string> = {
  image: '/fingerprint/image',
  video: '/fingerprint/video',
  audio: '/fingerprint/audio',
};

const ACCEPTS: Record<ContentType, string> = {
  image: 'image/*',
  video: 'video/*',
  audio: 'audio/*',
};

function normalizeBaseUrl(baseUrl: string) {
  return baseUrl.replace(/\/+$/, '');
}

export default function ContentRegistrationModal({ isOpen, onClose, userId, userName }: ContentRegistrationModalProps) {
  const [contentType, setContentType] = useState<ContentType>('image');
  const [contentFile, setContentFile] = useState<File | null>(null);
  const [licenseFile, setLicenseFile] = useState<File | null>(null);
  const [assetId, setAssetId] = useState('');
  const [source, setSource] = useState('');
  const [contentLabel, setContentLabel] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [result, setResult] = useState<unknown>(null);

  const accept = useMemo(() => ACCEPTS[contentType], [contentType]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    setError('');
    setSuccessMessage('');
    setResult(null);
  }, [isOpen]);

  const handleContentFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setContentFile(event.target.files?.[0] ?? null);
    setError('');
  };

  const handleLicenseFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setLicenseFile(event.target.files?.[0] ?? null);
    setError('');
  };

  const resetForm = () => {
    setContentType('image');
    setContentFile(null);
    setLicenseFile(null);
    setAssetId('');
    setSource('');
    setContentLabel('');
    setError('');
    setSuccessMessage('');
    setResult(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');

    if (!contentFile) {
      setError('Please upload a content file first.');
      return;
    }

    if (!licenseFile) {
      setError('Please upload a license file.');
      return;
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('file', contentFile);
      formData.append('register', 'true');
      formData.append('user_id', userId);

      if (assetId.trim()) {
        formData.append('asset_id', assetId.trim());
      }

      if (source.trim()) {
        formData.append('source', source.trim());
      }

      if (contentLabel.trim()) {
        formData.append('title', contentLabel.trim());
      }

      formData.append('license', licenseFile);
      formData.append('license_name', licenseFile.name);

      const response = await fetch(`${normalizeBaseUrl(API_BASE_URL)}${ENDPOINTS[contentType]}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(responseText || `Content registration failed (${response.status})`);
      }

      const payload = await response.json();
      setResult(payload);
      setSuccessMessage('Content registered successfully.');
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Content registration failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 px-4 py-6 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-2xl">
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-violet-500" />

        <div className="max-h-[90vh] overflow-y-auto p-6 sm:p-8">
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.32em] text-slate-400">Content Registration</p>
              <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">Register your protected content</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Upload a video, image, or audio asset together with a license file so the asset can be registered against your account.
              </p>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
            >
              Close
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2">
                <label htmlFor="contentType" className="text-sm font-semibold text-slate-900">
                  Content type
                </label>
                <select
                  id="contentType"
                  value={contentType}
                  onChange={(e) => setContentType(e.target.value as ContentType)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="image">Image</option>
                  <option value="video">Video</option>
                  <option value="audio">Audio</option>
                </select>
              </div>

              <div className="space-y-2 sm:col-span-2">
                <label htmlFor="contentFile" className="text-sm font-semibold text-slate-900">
                  Upload {contentType}
                </label>
                <input
                  id="contentFile"
                  type="file"
                  accept={accept}
                  onChange={handleContentFileChange}
                  className="w-full rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-700 file:mr-4 file:rounded-xl file:border-0 file:bg-accent file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:bg-slate-100"
                />
                <p className="text-xs text-slate-500">Accepted format: {accept.replace('/*', '')}.</p>
              </div>

              <div className="space-y-2 sm:col-span-2">
                <label htmlFor="licenseFile" className="text-sm font-semibold text-slate-900">
                  Upload license
                </label>
                <input
                  id="licenseFile"
                  type="file"
                  onChange={handleLicenseFileChange}
                  className="w-full rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-700 file:mr-4 file:rounded-xl file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:bg-slate-100"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="contentLabel" className="text-sm font-semibold text-slate-900">
                  Content title
                </label>
                <input
                  id="contentLabel"
                  type="text"
                  value={contentLabel}
                  onChange={(e) => setContentLabel(e.target.value)}
                  placeholder="Campaign poster, promo video, podcast episode"
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="assetId" className="text-sm font-semibold text-slate-900">
                  Asset ID
                </label>
                <input
                  id="assetId"
                  type="text"
                  value={assetId}
                  onChange={(e) => setAssetId(e.target.value)}
                  placeholder="Optional custom identifier"
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div className="space-y-2 sm:col-span-2">
                <label htmlFor="source" className="text-sm font-semibold text-slate-900">
                  Source / rights holder
                </label>
                <input
                  id="source"
                  type="text"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  placeholder="Studio name, creator, website, or provenance note"
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              <p className="font-semibold text-slate-900">Account</p>
              <p className="mt-1">{userName ? `${userName} · ` : ''}{userId}</p>
            </div>

            {error && <div className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
            {successMessage && (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
                {successMessage}
              </div>
            )}

            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={() => {
                  resetForm();
                  onClose();
                }}
                className="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 font-semibold text-slate-900 transition hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 rounded-2xl bg-accent px-4 py-3 font-semibold text-white shadow-lg shadow-accent/20 transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {isSubmitting ? 'Registering...' : 'Register content'}
              </button>
            </div>

            {result && (
              <details className="rounded-3xl border border-slate-200 bg-white p-4">
                <summary className="cursor-pointer text-sm font-semibold text-slate-900">Registration response</summary>
                <pre className="mt-3 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </details>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}