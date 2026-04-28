import { useEffect, useRef, useState, useCallback } from 'react';

export type HITLMessage = {
  id: string;
  priority: number;
  timestamp: number;
  payload: Record<string, unknown>;
};

interface UseHITLOptions {
  url?: string;
  reconnectMs?: number;
}

// Hook optimized for high-frequency updates: batches updates with rAF
export function useHITLWebSocket(options?: UseHITLOptions) {
  const url = options?.url || (typeof window !== 'undefined' ? `${location.origin.replace(/^http/, 'ws')}/ws/hitl` : '');
  const reconnectMs = options?.reconnectMs ?? 2000;

  const wsRef = useRef<WebSocket | null>(null);
  const bufferRef = useRef<HITLMessage[]>([]);
  const [messages, setMessages] = useState<HITLMessage[]>([]);
  const connectedRef = useRef(false);
  const rafRef = useRef<number | null>(null);
  const reconnectTimer = useRef<number | null>(null);

  const flush = useCallback(() => {
    if (bufferRef.current.length === 0) return;
    // merge-buffer - keep most recent per id
    const map = new Map<string, HITLMessage>();
    for (const m of bufferRef.current) map.set(m.id, m);
    bufferRef.current = [];
    setMessages(prev => {
      // Prepend new messages, but keep array sized to 1000 for performance
      const merged = Array.from(map.values()).concat(prev);
      return merged.slice(0, 1000);
    });
  }, []);

  useEffect(() => {
    const tick = () => {
      flush();
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [flush]);

  useEffect(() => {
    let closedByUser = false;
    function connect() {
      if (!url) return;
      wsRef.current = new WebSocket(url);
      wsRef.current.onopen = () => {
        connectedRef.current = true;
      };
      wsRef.current.onmessage = ev => {
        try {
          const parsed = JSON.parse(ev.data) as HITLMessage | HITLMessage[];
          if (Array.isArray(parsed)) bufferRef.current.push(...parsed);
          else bufferRef.current.push(parsed);
        } catch (e) {
          // ignore malformed
        }
      };
      wsRef.current.onclose = () => {
        connectedRef.current = false;
        if (!closedByUser) {
          reconnectTimer.current = window.setTimeout(connect, reconnectMs);
        }
      };
      wsRef.current.onerror = () => {
        // swallow - onclose will schedule reconnect
      };
    }
    connect();
    return () => {
      closedByUser = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [url, reconnectMs]);

  return {
    messages,
    connected: connectedRef.current,
    clear: () => setMessages([]),
  } as const;
}

export default useHITLWebSocket;
