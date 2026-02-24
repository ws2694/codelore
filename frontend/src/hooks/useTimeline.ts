import { useState, useCallback } from 'react';
import { exploreApi } from '../lib/api';
import type { TimelineEntry, Decision } from '../lib/types';

export function useTimeline() {
  const [entries, setEntries] = useState<TimelineEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchedPath, setSearchedPath] = useState('');

  const searchTimeline = useCallback(async (filepath: string) => {
    setError(null);
    setIsLoading(true);
    setSearchedPath(filepath);

    try {
      const result = await exploreApi.getTimeline(filepath);
      setEntries(result.entries);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch timeline';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { entries, isLoading, error, searchTimeline, searchedPath };
}

export function useDecisions() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchDecisions = useCallback(async (query?: string) => {
    setIsLoading(true);
    try {
      const result = await exploreApi.getDecisions(query);
      setDecisions(result.decisions);
    } catch {
      // Silently handle
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { decisions, isLoading, fetchDecisions };
}
