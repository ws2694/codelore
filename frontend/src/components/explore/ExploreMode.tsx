import { useState, useEffect } from 'react';
import { GitBranch, Search, Lightbulb, TrendingUp, Users, Shield, Sparkles, X } from 'lucide-react';
import { useTimeline, useDecisions, useSemanticSearch, useExperts, useImpact } from '../../hooks/useTimeline';
import { exploreApi } from '../../lib/api';
import Timeline from './Timeline';
import DecisionGraph from './DecisionGraph';
import SemanticResults from './SemanticResults';
import ExpertPanel from './ExpertPanel';
import ImpactPanel from './ImpactPanel';
import { LoadingSkeleton } from '../shared/LoadingState';

type ExploreTab = 'timeline' | 'decisions' | 'experts' | 'impact' | 'semantic';

const TAB_CONFIG: Record<ExploreTab, { icon: typeof TrendingUp; label: string; placeholder: string }> = {
  timeline:  { icon: TrendingUp, label: 'Timeline',  placeholder: 'Enter file path (e.g., src/auth/jwt.ts)' },
  decisions: { icon: Lightbulb,  label: 'Decisions',  placeholder: 'Search decisions...' },
  experts:   { icon: Users,      label: 'Experts',    placeholder: 'Enter module or file path (e.g., src/auth)' },
  impact:    { icon: Shield,     label: 'Impact',     placeholder: 'Enter file path for impact analysis' },
  semantic:  { icon: Sparkles,   label: 'Semantic',   placeholder: 'Ask a conceptual question (e.g., why did we choose Redis?)' },
};

export default function ExploreMode() {
  const [tab, setTab] = useState<ExploreTab>('timeline');
  const [searchInput, setSearchInput] = useState('');
  const [activeDecisionQuery, setActiveDecisionQuery] = useState('');
  const { entries, isLoading: timelineLoading, error: timelineError, searchTimeline, searchedPath } = useTimeline();
  const { decisions, isLoading: decisionsLoading, fetchDecisions } = useDecisions();
  const { results: semanticResults, isLoading: semanticLoading, error: semanticError, search: semanticSearch, searchedQuery } = useSemanticSearch();
  const { result: expertResult, isLoading: expertsLoading, error: expertsError, searchExperts, searchedModule } = useExperts();
  const { analysis: impactAnalysis, isLoading: impactLoading, error: impactError, analyzeImpact, searchedPath: impactPath } = useImpact();

  useEffect(() => {
    fetchDecisions();
  }, [fetchDecisions]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const query = searchInput.trim();
    if (!query) return;
    if (tab === 'timeline') {
      searchTimeline(query);
    } else if (tab === 'decisions') {
      setActiveDecisionQuery(query);
      fetchDecisions(query);
    } else if (tab === 'experts') {
      searchExperts(query);
    } else if (tab === 'impact') {
      analyzeImpact(query);
    } else if (tab === 'semantic') {
      semanticSearch(query);
    }
  };

  const clearDecisionSearch = () => {
    setSearchInput('');
    setActiveDecisionQuery('');
    fetchDecisions();
  };

  const handleImpactFileClick = (path: string) => {
    setTab('timeline');
    setSearchInput(path);
    searchTimeline(path);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800/50 shrink-0">
        <div className="flex items-center gap-3 mb-4">
          <GitBranch className="w-5 h-5 text-brand-400" />
          <div>
            <h2 className="font-semibold text-white">Explore</h2>
            <p className="text-xs text-gray-500">Code archaeology and decision timeline</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-4 overflow-x-auto">
          {(Object.keys(TAB_CONFIG) as ExploreTab[]).map((key) => {
            const cfg = TAB_CONFIG[key];
            const Icon = cfg.icon;
            return (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors whitespace-nowrap ${
                  tab === key
                    ? 'bg-brand-600/20 text-brand-300 border border-brand-500/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {cfg.label}
              </button>
            );
          })}
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder={TAB_CONFIG[tab].placeholder}
              className="w-full bg-gray-800/50 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-brand-500/50 transition-colors"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 rounded-lg text-sm font-medium transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {tab === 'timeline' ? (
          timelineLoading ? (
            <LoadingSkeleton lines={6} />
          ) : timelineError ? (
            <div className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
              {timelineError}
            </div>
          ) : entries.length > 0 ? (
            <div>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-sm text-gray-400">
                  History for <code className="text-brand-300">{searchedPath}</code>
                </h3>
                <span className="text-xs text-gray-500">{entries.length} events</span>
              </div>
              <Timeline entries={entries} />
            </div>
          ) : searchedPath ? (
            <div className="text-center py-12 text-gray-500 text-sm">
              No history found for <code className="text-brand-300">{searchedPath}</code>
            </div>
          ) : (
            <EmptyExplore onSelect={(path) => { setSearchInput(path); searchTimeline(path); }} />
          )

        ) : tab === 'decisions' ? (
          decisionsLoading ? (
            <LoadingSkeleton lines={5} />
          ) : decisions.length > 0 ? (
            <div>
              {activeDecisionQuery && (
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm text-gray-400">
                    Results for <code className="text-brand-300">{activeDecisionQuery}</code>
                  </h3>
                  <button
                    onClick={clearDecisionSearch}
                    className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 px-2 py-1 rounded hover:bg-gray-800 transition-colors"
                  >
                    <X className="w-3 h-3" />
                    Clear search
                  </button>
                </div>
              )}
              <DecisionGraph decisions={decisions} />
            </div>
          ) : activeDecisionQuery ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-sm mb-3">
                No decisions matching <code className="text-brand-300">{activeDecisionQuery}</code>
              </p>
              <button
                onClick={clearDecisionSearch}
                className="text-sm text-brand-400 hover:text-brand-300 transition-colors"
              >
                Show all decisions
              </button>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500 text-sm">
              No decisions found. Ingest a repository to populate this view.
            </div>
          )

        ) : tab === 'experts' ? (
          expertsLoading ? (
            <LoadingSkeleton lines={5} />
          ) : expertsError ? (
            <div className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
              {expertsError}
            </div>
          ) : expertResult ? (
            <div>
              <div className="mb-4">
                <h3 className="text-sm text-gray-400">
                  Experts for <code className="text-brand-300">{searchedModule}</code>
                </h3>
              </div>
              <ExpertPanel result={expertResult} />
            </div>
          ) : (
            <EmptyExperts />
          )

        ) : tab === 'impact' ? (
          impactLoading ? (
            <LoadingSkeleton lines={6} />
          ) : impactError ? (
            <div className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
              {impactError}
            </div>
          ) : impactAnalysis ? (
            <div>
              <div className="mb-4">
                <h3 className="text-sm text-gray-400">
                  Impact analysis for <code className="text-brand-300">{impactPath}</code>
                </h3>
              </div>
              <ImpactPanel analysis={impactAnalysis} onFileClick={handleImpactFileClick} />
            </div>
          ) : (
            <EmptyImpact />
          )

        ) : tab === 'semantic' ? (
          semanticLoading ? (
            <LoadingSkeleton lines={6} />
          ) : semanticError ? (
            <div className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
              {semanticError}
            </div>
          ) : semanticResults.length > 0 ? (
            <div>
              <div className="mb-4">
                <h3 className="text-sm text-gray-400">
                  Semantic results for <code className="text-brand-300">{searchedQuery}</code>
                </h3>
              </div>
              <SemanticResults results={semanticResults} />
            </div>
          ) : searchedQuery ? (
            <div className="text-center py-12 text-gray-500 text-sm">
              No semantic matches for <code className="text-brand-300">{searchedQuery}</code>
            </div>
          ) : (
            <EmptySemantic />
          )
        ) : null}
      </div>
    </div>
  );
}

// ── Empty States ────────────────────────────────────────────────────────

function EmptyExplore({ onSelect }: { onSelect: (path: string) => void }) {
  const [popularFiles, setPopularFiles] = useState<{ path: string; commits: number }[]>([]);

  useEffect(() => {
    exploreApi.getPopularFiles(8).then((res) => setPopularFiles(res.files)).catch(() => {});
  }, []);

  return (
    <div className="flex flex-col items-center justify-center h-full max-w-lg mx-auto text-center">
      <GitBranch className="w-12 h-12 text-gray-700 mb-4" />
      <h3 className="text-lg font-medium text-gray-300 mb-2">Code Archaeology</h3>
      <p className="text-sm text-gray-500 mb-6">
        Search for a file or directory to see its complete history — every commit, PR, and decision that shaped it.
      </p>
      {popularFiles.length > 0 ? (
        <div className="space-y-1.5 w-full">
          <p className="text-xs text-gray-600 uppercase tracking-wider mb-2">Most active files:</p>
          {popularFiles.map((f) => (
            <button
              key={f.path}
              onClick={() => onSelect(f.path)}
              className="w-full text-left flex items-center justify-between text-sm text-gray-400 bg-gray-800/30 hover:bg-gray-800/60 rounded-lg px-3 py-2 font-mono transition-colors"
            >
              <span className="truncate">{f.path}</span>
              <span className="text-xs text-gray-600 shrink-0 ml-2">{f.commits} commits</span>
            </button>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-600">Ingest a repository to see file history.</p>
      )}
    </div>
  );
}

function EmptyExperts() {
  return (
    <div className="flex flex-col items-center justify-center h-full max-w-md mx-auto text-center">
      <Users className="w-12 h-12 text-gray-700 mb-4" />
      <h3 className="text-lg font-medium text-gray-300 mb-2">Expert Finder</h3>
      <p className="text-sm text-gray-500">
        Search for a module or file path to find the top contributors and on-call recommendation.
      </p>
    </div>
  );
}

function EmptyImpact() {
  return (
    <div className="flex flex-col items-center justify-center h-full max-w-md mx-auto text-center">
      <Shield className="w-12 h-12 text-gray-700 mb-4" />
      <h3 className="text-lg font-medium text-gray-300 mb-2">Impact Analysis</h3>
      <p className="text-sm text-gray-500">
        Enter a file path to analyze its change impact — co-change patterns, coupling risk, bus factor, and who to contact.
      </p>
    </div>
  );
}

function EmptySemantic() {
  return (
    <div className="flex flex-col items-center justify-center h-full max-w-md mx-auto text-center">
      <Sparkles className="w-12 h-12 text-gray-700 mb-4" />
      <h3 className="text-lg font-medium text-gray-300 mb-2">Semantic Search</h3>
      <p className="text-sm text-gray-500">
        Ask a conceptual question to find related commits, PRs, decisions, and docs using vector similarity — no exact keywords needed.
      </p>
    </div>
  );
}
