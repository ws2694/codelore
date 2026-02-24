import { Phone, AlertTriangle, Shield, ShieldCheck, User } from 'lucide-react';
import type { Expert, ExpertFinderResult } from '../../lib/types';

export function OnCallCard({ expert, label }: { expert: Expert; label?: string }) {
  const date = expert.last_active ? new Date(expert.last_active) : null;

  return (
    <div className="glass-panel p-4 border-brand-500/30 glow-brand">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-brand-500/20 border border-brand-500/40 flex items-center justify-center">
            <Phone className="w-4 h-4 text-brand-400" />
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">{label || 'On-Call Recommendation'}</p>
            <p className="text-sm font-semibold text-white mt-0.5">@{expert.author}</p>
          </div>
        </div>
        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-green-400/10 text-green-400 border border-green-400/30">
          Recommended
        </span>
      </div>
      <div className="flex items-center gap-4 mt-3 ml-[52px] text-xs text-gray-400">
        <span>{expert.commits} commits</span>
        {expert.recent_commits !== undefined && <span>{expert.recent_commits} in last 90d</span>}
        {date && <span>Active {formatRelativeDate(date)}</span>}
      </div>
    </div>
  );
}

function BusFactorBadge({ count }: { count: number }) {
  const style =
    count <= 1
      ? { color: 'text-red-400', bg: 'bg-red-400/10', border: 'border-red-400/30', icon: AlertTriangle, label: 'Single point of failure' }
      : count === 2
      ? { color: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/30', icon: Shield, label: 'Low bus factor' }
      : { color: 'text-green-400', bg: 'bg-green-400/10', border: 'border-green-400/30', icon: ShieldCheck, label: 'Healthy' };

  const Icon = style.icon;

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${style.bg} border ${style.border}`}>
      <Icon className={`w-4 h-4 ${style.color}`} />
      <div>
        <p className={`text-xs font-medium ${style.color}`}>Bus Factor: {count}</p>
        <p className="text-[10px] text-gray-500">{style.label}</p>
      </div>
    </div>
  );
}

function ExpertCard({ expert, rank, totalCommits }: { expert: Expert; rank: number; totalCommits: number }) {
  const date = expert.last_active ? new Date(expert.last_active) : null;
  const pct = totalCommits > 0 ? Math.round((expert.commits / totalCommits) * 100) : 0;
  const initial = expert.author.charAt(0).toUpperCase();

  return (
    <div className="glass-panel p-4 hover:border-gray-700 transition-colors">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center shrink-0">
          <span className="text-xs font-bold text-gray-300">{initial}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-200">@{expert.author}</span>
              {rank === 1 && (
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/30">
                  Top
                </span>
              )}
            </div>
            <span className="text-xs text-gray-500 font-mono">{pct}%</span>
          </div>

          <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden mb-2">
            <div
              className="h-full bg-brand-500/60 rounded-full transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>

          <div className="flex items-center gap-3 text-[11px] text-gray-500">
            <span>{expert.commits} commits</span>
            {expert.recent_commits !== undefined && <span>{expert.recent_commits} recent</span>}
            {date && <span>Active {formatRelativeDate(date)}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ExpertPanel({ result }: { result: ExpertFinderResult }) {
  return (
    <div className="space-y-4">
      {result.on_call && <OnCallCard expert={result.on_call} />}

      <div className="flex gap-3">
        <BusFactorBadge count={result.bus_factor} />
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700/50">
          <User className="w-4 h-4 text-gray-400" />
          <div>
            <p className="text-xs font-medium text-gray-300">{result.total_commits}</p>
            <p className="text-[10px] text-gray-500">Total commits</p>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-xs text-gray-500 uppercase tracking-wider">Contributors</p>
        {result.experts.map((e, i) => (
          <ExpertCard key={e.author} expert={e} rank={i + 1} totalCommits={result.total_commits} />
        ))}
      </div>
    </div>
  );
}

function formatRelativeDate(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'today';
  if (diffDays === 1) return 'yesterday';
  if (diffDays < 30) return `${diffDays}d ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`;
  return `${Math.floor(diffDays / 365)}y ago`;
}
