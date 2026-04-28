export interface ApiOptions {
  baseUrl?: string;
  headers?: Record<string, string>;
}

const DEFAULT_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api';

export async function apiFetch<T = unknown>(path: string, opts?: RequestInit, options?: ApiOptions): Promise<T> {
  const base = options?.baseUrl || DEFAULT_BASE;
  const res = await fetch(`${base}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}
