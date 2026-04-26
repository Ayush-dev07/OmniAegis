import { useCallback, useEffect, useRef, useState } from 'react';

export interface HITLQueueUpdate {
  type: 'queue_depth' | 'item_completed' | 'heartbeat' | 'assignment_ready';
  payload?: Record<string, unknown>;
  timestamp: number;
}

export interface UseHITLWebSocketOptions {
  url?: string;
  onQueueDepthChange?: (depth: number) => void;
  onItemCompleted?: (itemId: string) => void;
  onHeartbeat?: () => void;
  onAssignmentReady?: (assignment: Record<string, unknown>) => void;
  autoReconnect?: boolean;
  reconnectDelay?: number;
}

export function useHITLWebSocket(options: UseHITLWebSocketOptions = {}) {
  const {
    url = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/hitl`,
    onQueueDepthChange,
    onItemCompleted,
    onHeartbeat,
    onAssignmentReady,
    autoReconnect = true,
    reconnectDelay = 3000,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data) as HITLQueueUpdate;

        switch (message.type) {
          case 'queue_depth':
            if (onQueueDepthChange && typeof message.payload?.depth === 'number') {
              onQueueDepthChange(message.payload.depth);
            }
            break;
          case 'item_completed':
            if (onItemCompleted && typeof message.payload?.item_id === 'string') {
              onItemCompleted(message.payload.item_id);
            }
            break;
          case 'heartbeat':
            if (onHeartbeat) {
              onHeartbeat();
            }
            break;
          case 'assignment_ready':
            if (onAssignmentReady && message.payload) {
              onAssignmentReady(message.payload);
            }
            break;
        }
      } catch (error) {
        console.error('Failed to parse HITL WebSocket message:', error);
      }
    },
    [onQueueDepthChange, onItemCompleted, onHeartbeat, onAssignmentReady],
  );

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(url);

      ws.addEventListener('open', () => {
        setIsConnected(true);
        setReconnectAttempt(0);
        console.log('[HITL] WebSocket connected');
      });

      ws.addEventListener('message', handleMessage);

      ws.addEventListener('close', () => {
        setIsConnected(false);
        console.log('[HITL] WebSocket closed');

        if (autoReconnect && reconnectAttempt < 10) {
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`[HITL] Reconnect attempt ${reconnectAttempt + 1}`);
            setReconnectAttempt((prev) => prev + 1);
            connect();
          }, reconnectDelay * Math.pow(1.5, reconnectAttempt));
        }
      });

      ws.addEventListener('error', (event) => {
        console.error('[HITL] WebSocket error:', event);
      });

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create HITL WebSocket:', error);
    }
  }, [url, autoReconnect, reconnectDelay, reconnectAttempt, handleMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback(
    (message: Record<string, unknown>) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(message));
      } else {
        console.warn('[HITL] WebSocket not connected, message not sent:', message);
      }
    },
    [],
  );

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    send,
    disconnect,
    reconnectAttempt,
  };
}
