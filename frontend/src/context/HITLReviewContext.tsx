import { ReactNode, createContext, useCallback, useContext, useReducer } from 'react';

export interface HITLReviewItem {
  item_id: string;
  asset_id: string;
  priority_score: number;
  assigned_to: string;
  lock_ttl_seconds: number;
  confidence?: number;
  content_type?: string;
  rights_node_ids?: string[];
  metadata?: Record<string, unknown>;
}

export interface HITLReviewDecision {
  item_id: string;
  decision: 'INFRINGING' | 'NOT_INFRINGING' | 'ESCALATE';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  notes?: string;
  decided_at_ms: number;
}

export interface HITLReviewState {
  currentItem: HITLReviewItem | null;
  currentDecision: HITLReviewDecision | null;
  lockExpiresAt: number | null;
  queueDepth: number;
  isLoading: boolean;
  error: string | null;
  saliencyOpacity: number;
  assignmentLockSecondsRemaining: number;
}

interface HITLReviewAction {
  type:
    | 'SET_CURRENT_ITEM'
    | 'SET_LOCK_EXPIRY'
    | 'SET_QUEUE_DEPTH'
    | 'SET_LOADING'
    | 'SET_ERROR'
    | 'SET_SALIENCY_OPACITY'
    | 'SET_ASSIGNMENT_LOCK_REMAINING'
    | 'SET_DECISION'
    | 'RESET_DECISION'
    | 'CLEAR_ITEM';
  payload?: unknown;
}

const initialState: HITLReviewState = {
  currentItem: null,
  currentDecision: null,
  lockExpiresAt: null,
  queueDepth: 0,
  isLoading: false,
  error: null,
  saliencyOpacity: 0.6,
  assignmentLockSecondsRemaining: 0,
};

function hitlReviewReducer(state: HITLReviewState, action: HITLReviewAction): HITLReviewState {
  switch (action.type) {
    case 'SET_CURRENT_ITEM':
      return {
        ...state,
        currentItem: action.payload as HITLReviewItem,
        error: null,
      };
    case 'SET_LOCK_EXPIRY':
      return {
        ...state,
        lockExpiresAt: action.payload as number,
      };
    case 'SET_QUEUE_DEPTH':
      return {
        ...state,
        queueDepth: action.payload as number,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload as boolean,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload as string,
      };
    case 'SET_SALIENCY_OPACITY':
      return {
        ...state,
        saliencyOpacity: action.payload as number,
      };
    case 'SET_ASSIGNMENT_LOCK_REMAINING':
      return {
        ...state,
        assignmentLockSecondsRemaining: action.payload as number,
      };
    case 'SET_DECISION':
      return {
        ...state,
        currentDecision: action.payload as HITLReviewDecision,
      };
    case 'RESET_DECISION':
      return {
        ...state,
        currentDecision: null,
      };
    case 'CLEAR_ITEM':
      return {
        ...state,
        currentItem: null,
        currentDecision: null,
        lockExpiresAt: null,
      };
    default:
      return state;
  }
}

interface HITLReviewContextType {
  state: HITLReviewState;
  setCurrentItem: (item: HITLReviewItem) => void;
  setLockExpiry: (expiresAt: number) => void;
  setQueueDepth: (depth: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSaliencyOpacity: (opacity: number) => void;
  setAssignmentLockRemaining: (seconds: number) => void;
  setDecision: (decision: HITLReviewDecision) => void;
  resetDecision: () => void;
  clearItem: () => void;
}

const HITLReviewContext = createContext<HITLReviewContextType | undefined>(undefined);

interface HITLReviewProviderProps {
  children: ReactNode;
}

export function HITLReviewProvider({ children }: HITLReviewProviderProps) {
  const [state, dispatch] = useReducer(hitlReviewReducer, initialState);

  const setCurrentItem = useCallback((item: HITLReviewItem) => {
    dispatch({ type: 'SET_CURRENT_ITEM', payload: item });
  }, []);

  const setLockExpiry = useCallback((expiresAt: number) => {
    dispatch({ type: 'SET_LOCK_EXPIRY', payload: expiresAt });
  }, []);

  const setQueueDepth = useCallback((depth: number) => {
    dispatch({ type: 'SET_QUEUE_DEPTH', payload: depth });
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  }, []);

  const setError = useCallback((error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  }, []);

  const setSaliencyOpacity = useCallback((opacity: number) => {
    dispatch({ type: 'SET_SALIENCY_OPACITY', payload: Math.min(Math.max(opacity, 0), 1) });
  }, []);

  const setAssignmentLockRemaining = useCallback((seconds: number) => {
    dispatch({ type: 'SET_ASSIGNMENT_LOCK_REMAINING', payload: Math.max(0, seconds) });
  }, []);

  const setDecision = useCallback((decision: HITLReviewDecision) => {
    dispatch({ type: 'SET_DECISION', payload: decision });
  }, []);

  const resetDecision = useCallback(() => {
    dispatch({ type: 'RESET_DECISION' });
  }, []);

  const clearItem = useCallback(() => {
    dispatch({ type: 'CLEAR_ITEM' });
  }, []);

  const value: HITLReviewContextType = {
    state,
    setCurrentItem,
    setLockExpiry,
    setQueueDepth,
    setLoading,
    setError,
    setSaliencyOpacity,
    setAssignmentLockRemaining,
    setDecision,
    resetDecision,
    clearItem,
  };

  return <HITLReviewContext.Provider value={value}>{children}</HITLReviewContext.Provider>;
}

export function useHITLReview(): HITLReviewContextType {
  const context = useContext(HITLReviewContext);
  if (!context) {
    throw new Error('useHITLReview must be used within HITLReviewProvider');
  }
  return context;
}
