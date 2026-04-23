import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { liveFeedEntries, threatQueue } from '@/data/mockData';
import type { FeedEntry, ThreatItem, ViewKey } from '@/types/dashboard';

type DateRange = {
  start: string;
  end: string;
};

type DashboardContextValue = {
  currentView: ViewKey;
  setCurrentView: (view: ViewKey) => void;
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  dateRange: DateRange;
  setDateRange: (range: DateRange) => void;
  selectedThreat: ThreatItem | null;
  setSelectedThreat: (item: ThreatItem | null) => void;
  filteredThreats: ThreatItem[];
  liveFeed: FeedEntry[];
  pushFeedEntry: (entry: FeedEntry) => void;
};

const DashboardContext = createContext<DashboardContextValue | undefined>(undefined);

const matchesSearch = (item: ThreatItem, term: string) => {
  if (!term.trim()) return true;
  const search = term.toLowerCase();
  return [item.id, item.title, item.assetName, item.source, item.region, item.category, item.status]
    .join(' ')
    .toLowerCase()
    .includes(search);
};

const isWithinDateRange = (_item: ThreatItem, range: DateRange) => {
  if (!range.start && !range.end) return true;

  const itemDate = new Date(_item.createdAt);
  if (range.start && itemDate < new Date(range.start)) return false;
  if (range.end) {
    const endDate = new Date(range.end);
    endDate.setHours(23, 59, 59, 999);
    if (itemDate > endDate) return false;
  }

  return true;
};

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [currentView, setCurrentView] = useState<ViewKey>('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [dateRange, setDateRange] = useState<DateRange>({ start: '', end: '' });
  const [selectedThreat, setSelectedThreat] = useState<ThreatItem | null>(null);
  const [liveFeed, setLiveFeed] = useState<FeedEntry[]>(liveFeedEntries);

  useEffect(() => {
    const timer = window.setInterval(() => {
      const generated: FeedEntry = {
        id: crypto.randomUUID(),
        timestamp: new Date().toLocaleTimeString([], { hour12: false }),
        message: 'SentinelAgent heartbeat acknowledged across all monitoring nodes.',
        level: 'info',
      };

      setLiveFeed((prev: FeedEntry[]) => [generated, ...prev].slice(0, 12));
    }, 8000);

    return () => window.clearInterval(timer);
  }, []);

  const filteredThreats = useMemo(
    () => threatQueue.filter((item) => matchesSearch(item, searchTerm) && isWithinDateRange(item, dateRange)),
    [searchTerm, dateRange],
  );

  useEffect(() => {
    if (filteredThreats.length === 0 && selectedThreat) {
      setSelectedThreat(null);
      return;
    }

    if (selectedThreat && !filteredThreats.some((item) => item.id === selectedThreat.id)) {
      setSelectedThreat(filteredThreats[0] ?? null);
    }
  }, [filteredThreats, selectedThreat]);

  const pushFeedEntry = (entry: FeedEntry) => {
    setLiveFeed((prev: FeedEntry[]) => [entry, ...prev].slice(0, 18));
  };

  const value = useMemo(
    () => ({
      currentView,
      setCurrentView,
      searchTerm,
      setSearchTerm,
      dateRange,
      setDateRange,
      selectedThreat,
      setSelectedThreat,
      filteredThreats,
      liveFeed,
      pushFeedEntry,
    }),
    [currentView, searchTerm, dateRange, selectedThreat, filteredThreats, liveFeed],
  );

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within DashboardProvider');
  }

  return context;
}