import { useState, useCallback } from 'react';
import { exploreApi } from '../lib/api';
import type { TimelineEntry, Decision, SemanticSearchResult, ExpertFinderResult, ImpactAnalysis } from '../lib/types';

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

export function useSemanticSearch() {
  const [results, setResults] = useState<SemanticSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchedQuery, setSearchedQuery] = useState('');

  const search = useCallback(async (query: string) => {
    setError(null);
    setIsLoading(true);
    setSearchedQuery(query);
    try {
      const result = await exploreApi.semanticSearch(query);
      setResults(result.results);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Semantic search failed';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { results, isLoading, error, search, searchedQuery };
}

export function useExperts() {
  const [result, setResult] = useState<ExpertFinderResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchedModule, setSearchedModule] = useState('');

  const searchExperts = useCallback(async (module: string) => {
    setError(null);
    setIsLoading(true);
    setSearchedModule(module);
    try {
      const data = await exploreApi.getExperts(module);
      setResult(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch experts';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { result, isLoading, error, searchExperts, searchedModule };
}

export function useImpact() {
  const [analysis, setAnalysis] = useState<ImpactAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchedPath, setSearchedPath] = useState('');

  const analyzeImpact = useCallback(async (filepath: string) => {
    setError(null);
    setIsLoading(true);
    setSearchedPath(filepath);
    try {
      const data = await exploreApi.getImpact(filepath);
      setAnalysis(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Impact analysis failed';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { analysis, isLoading, error, analyzeImpact, searchedPath };
}
