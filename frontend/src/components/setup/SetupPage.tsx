import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Github,
  Lock,
  Unlock,
  Star,
  Loader2,
  Check,
  Search,
  FolderGit2,
  ArrowRight,
  AlertCircle,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { authApi, githubApi, ingestApi } from '../../lib/api';
import type { GitHubRepo } from '../../lib/types';

export default function SetupPage() {
  const { auth, refresh } = useAuth();
  const navigate = useNavigate();

  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [isLoadingRepos, setIsLoadingRepos] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);
  const [ingesting, setIngesting] = useState(false);
  const [ingestStats, setIngestStats] = useState<Record<string, number> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // If already set up with env method + repo, allow skipping
  const canSkip = auth?.authenticated && auth.method === 'env' && !!auth.selected_repo;

  useEffect(() => {
    if (auth?.authenticated && auth.method === 'oauth') {
      loadRepos();
    }
  }, [auth?.authenticated, auth?.method]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleSignIn = async () => {
    setError(null);
    try {
      const { url } = await authApi.getGitHubUrl();
      window.location.href = url;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get GitHub auth URL');
    }
  };

  const loadRepos = async () => {
    setIsLoadingRepos(true);
    setError(null);
    try {
      const result = await githubApi.listRepos(1, 100);
      setRepos(result.repos);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load repos');
    } finally {
      setIsLoadingRepos(false);
    }
  };

  const handleSelectAndIngest = async (repoFullName: string) => {
    setSelectedRepo(repoFullName);
    setIngesting(true);
    setError(null);
    setIngestStats(null);

    try {
      await authApi.selectRepo(repoFullName);
      await ingestApi.trigger(repoFullName);

      pollRef.current = setInterval(async () => {
        try {
          const status = await ingestApi.status();
          if (status.last_stats) {
            setIngestStats(status.last_stats);
          }
          if (!status.running) {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;
            setIngesting(false);
            await refresh();
            navigate('/ask');
          }
        } catch {
          // keep polling
        }
      }, 2000);
    } catch (err: any) {
      setIngesting(false);
      setSelectedRepo(null);
      setError(err.response?.data?.detail || 'Failed to start ingestion');
    }
  };

  const filteredRepos = repos.filter(
    (r) =>
      r.full_name.toLowerCase().includes(searchFilter.toLowerCase()) ||
      r.description.toLowerCase().includes(searchFilter.toLowerCase()),
  );

  // Phase 3: Ingesting
  if (ingesting && selectedRepo) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="glass-panel p-10 max-w-lg w-full text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-brand-600/20 border border-brand-500/30 flex items-center justify-center mx-auto">
            <Loader2 className="w-8 h-8 text-brand-400 animate-spin" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white mb-2">Indexing repository</h2>
            <p className="text-gray-400 text-sm font-mono">{selectedRepo}</p>
          </div>
          <p className="text-gray-500 text-sm">
            Fetching commits, pull requests, and documentation...
          </p>
          {ingestStats && (
            <div className="grid grid-cols-3 gap-3 text-center">
              {Object.entries(ingestStats).map(([key, val]) => (
                <div key={key} className="bg-gray-800/50 rounded-lg p-3">
                  <p className="text-lg font-bold text-brand-300">{val}</p>
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider">{key}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Phase 2: Authenticated — pick a repo
  if (auth?.authenticated && auth.method === 'oauth') {
    return (
      <div className="min-h-screen flex flex-col p-6">
        <div className="max-w-3xl w-full mx-auto flex-1">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold text-sm">
                CL
              </div>
              <div>
                <h1 className="text-lg font-semibold text-white">Select a repository</h1>
                <p className="text-xs text-gray-500">Choose the codebase you want to explore</p>
              </div>
            </div>
            {auth.user && (
              <div className="flex items-center gap-2">
                {auth.avatar_url && (
                  <img src={auth.avatar_url} alt="" className="w-7 h-7 rounded-full" />
                )}
                <span className="text-sm text-gray-400">@{auth.user}</span>
              </div>
            )}
          </div>

          {error && (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 mb-4 text-red-300 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          {/* Search */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search repositories..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full bg-gray-900/60 border border-gray-800/50 rounded-lg pl-10 pr-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-brand-500/50"
            />
          </div>

          {/* Repo grid */}
          {isLoadingRepos ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-6 h-6 text-brand-400 animate-spin" />
              <span className="ml-2 text-gray-400 text-sm">Loading repositories...</span>
            </div>
          ) : (
            <div className="grid gap-2">
              {filteredRepos.map((repo) => (
                <button
                  key={repo.full_name}
                  onClick={() => handleSelectAndIngest(repo.full_name)}
                  className="glass-panel p-4 text-left hover:border-brand-500/40 hover:bg-brand-600/5 transition-all group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <FolderGit2 className="w-4 h-4 text-gray-500 shrink-0" />
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-white text-sm truncate">
                            {repo.full_name}
                          </span>
                          {repo.private ? (
                            <Lock className="w-3 h-3 text-yellow-500 shrink-0" />
                          ) : (
                            <Unlock className="w-3 h-3 text-gray-600 shrink-0" />
                          )}
                        </div>
                        {repo.description && (
                          <p className="text-xs text-gray-500 truncate mt-0.5">
                            {repo.description}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0 ml-4">
                      {repo.language && (
                        <span className="text-[10px] text-gray-500 bg-gray-800 px-2 py-0.5 rounded">
                          {repo.language}
                        </span>
                      )}
                      {repo.stars > 0 && (
                        <span className="flex items-center gap-1 text-[10px] text-gray-500">
                          <Star className="w-3 h-3" />
                          {repo.stars}
                        </span>
                      )}
                      <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-brand-400 transition-colors" />
                    </div>
                  </div>
                </button>
              ))}
              {filteredRepos.length === 0 && !isLoadingRepos && (
                <p className="text-center text-gray-500 py-10 text-sm">
                  {searchFilter ? 'No matching repositories found.' : 'No repositories found.'}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Phase 1: Not authenticated — sign in
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="glass-panel p-10 max-w-md w-full text-center space-y-8">
        {/* Logo */}
        <div>
          <div className="w-14 h-14 rounded-2xl bg-brand-600 flex items-center justify-center text-white font-bold text-lg mx-auto mb-4">
            CL
          </div>
          <h1 className="text-2xl font-bold text-white">CodeLore</h1>
          <p className="text-gray-500 text-sm mt-1">Codebase Memory Agent</p>
        </div>

        <div className="space-y-3">
          <p className="text-gray-300 text-sm">
            Connect your GitHub account to explore the history and decisions behind your codebase.
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-300 text-sm text-left">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        {auth?.oauth_configured ? (
          <button
            onClick={handleSignIn}
            className="w-full flex items-center justify-center gap-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            <Github className="w-5 h-5" />
            Sign in with GitHub
          </button>
        ) : (
          <div className="space-y-3 text-left">
            <p className="text-yellow-400 text-sm">
              GitHub OAuth is not configured yet.
            </p>
            <div className="bg-gray-800/50 rounded-lg p-4 text-xs text-gray-400 space-y-2">
              <p>1. Register an OAuth App at <span className="text-brand-300">github.com/settings/applications/new</span></p>
              <p>2. Set callback URL to <span className="text-brand-300 font-mono">http://localhost:3000/auth/callback</span></p>
              <p>3. Add to your <span className="text-brand-300 font-mono">.env</span> file:</p>
              <pre className="bg-gray-900 rounded p-2 text-gray-300 font-mono">
{`GITHUB_CLIENT_ID=your_id
GITHUB_CLIENT_SECRET=your_secret`}
              </pre>
              <p>4. Restart the backend server</p>
            </div>
          </div>
        )}

        {canSkip && (
          <button
            onClick={() => navigate('/ask')}
            className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
          >
            Skip — use .env configuration
          </button>
        )}
      </div>
    </div>
  );
}
