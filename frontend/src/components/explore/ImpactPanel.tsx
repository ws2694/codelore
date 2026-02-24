import { AlertTriangle, Shield, ShieldCheck, FileCode, BarChart3 } from 'lucide-react';
import { OnCallCard } from './ExpertPanel';
import type { ImpactAnalysis } from '../../lib/types';

function RiskBanner({ analysis }: { analysis: ImpactAnalysis }) {
  const r = analysis.risk_level;
  const style =
    r.level === 'high'
      ? { color: 'text-red-400', bg: 'bg-red-400/5', border: 'border-red-400/30', icon: AlertTriangle }
      : r.level === 'medium'
      ? { color: 'text-yellow-400', bg: 'bg-yellow-400/5', border: 'border-yellow-400/30', icon: Shield }
      : { color: 'text-green-400', bg: 'bg-green-400/5', border: 'border-green-400/30', icon: ShieldCheck };

  const Icon = style.icon;

  return (
    <div className={`glass-panel p-4 ${style.border} ${style.bg}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className={`w-5 h-5 ${style.color}`} />
          <h3 className={`text-sm font-semibold uppercase ${style.color}`}>
            {r.level} Risk
          </h3>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-400">
          <span>{analysis.total_commits} commits</span>
          <span>Bus factor: {analysis.bus_factor}</span>
          {analysis.latest_change && (
            <span>Last: {new Date(analysis.latest_change).toLocaleDateString()}</span>
          )}
        </div>
      </div>

      {r.factors.length > 0 && (
        <ul className="space-y-1 ml-7">
          {r.factors.map((f, i) => (
            <li key={i} className="text-xs text-gray-400 list-disc">{f}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function CoChangeList({ coChanges, onFileClick }: { coChanges: ImpactAnalysis['co_changes']; onFileClick?: (path: string) => void }) {
  if (coChanges.length === 0) return null;

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <FileCode className="w-4 h-4 text-gray-400" />
        <p className="text-xs text-gray-500 uppercase tracking-wider">Co-Change Patterns</p>
      </div>
      <div className="space-y-1.5">
        {coChanges.map((c) => {
          const pct = Math.round(c.coupling_ratio * 100);
          return (
            <div key={c.path} className="glass-panel px-3 py-2 hover:border-gray-700 transition-colors">
              <div className="flex items-center justify-between mb-1">
                <button
                  onClick={() => onFileClick?.(c.path)}
                  className="text-xs font-mono text-gray-300 hover:text-brand-300 transition-colors truncate text-left"
                >
                  {c.path}
                </button>
                <span className="text-[10px] text-gray-500 shrink-0 ml-2">
                  {c.shared_commits} shared · {pct}%
                </span>
              </div>
              <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${pct}%`,
                    backgroundColor: pct > 70 ? '#f87171' : pct > 40 ? '#fbbf24' : '#a78bfa',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ChangeFrequencyChart({ frequency }: { frequency: ImpactAnalysis['change_frequency'] }) {
  if (frequency.length === 0) return null;
  const maxCount = Math.max(...frequency.map((f) => f.count));

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <BarChart3 className="w-4 h-4 text-gray-400" />
        <p className="text-xs text-gray-500 uppercase tracking-wider">Change Frequency</p>
      </div>
      <div className="glass-panel p-4">
        <div className="flex items-end gap-1 h-20">
          {frequency.map((f) => {
            const height = maxCount > 0 ? (f.count / maxCount) * 100 : 0;
            const date = new Date(f.month);
            const label = date.toLocaleDateString('en-US', { month: 'short' });
            return (
              <div key={f.month} className="flex-1 flex flex-col items-center gap-1">
                <span className="text-[9px] text-gray-500 font-mono">{f.count}</span>
                <div className="w-full flex justify-center" style={{ height: '60px' }}>
                  <div
                    className="w-full max-w-[20px] bg-brand-500/40 rounded-t hover:bg-brand-500/60 transition-colors"
                    style={{ height: `${height}%`, minHeight: f.count > 0 ? '4px' : '0px' }}
                  />
                </div>
                <span className="text-[9px] text-gray-600">{label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function CompactExpertList({ experts }: { experts: ImpactAnalysis['experts'] }) {
  if (experts.length === 0) return null;

  return (
    <div>
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Top Contributors</p>
      <div className="flex flex-wrap gap-2">
        {experts.map((e) => {
          const date = e.last_active ? new Date(e.last_active) : null;
          return (
            <div
              key={e.author}
              className="glass-panel px-3 py-2 flex items-center gap-2 hover:border-gray-700 transition-colors"
            >
              <div className="w-6 h-6 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center">
                <span className="text-[10px] font-bold text-gray-300">{e.author.charAt(0).toUpperCase()}</span>
              </div>
              <div>
                <p className="text-xs font-medium text-gray-300">@{e.author}</p>
                <p className="text-[10px] text-gray-500">
                  {e.commits} commits
                  {date && ` · ${date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}`}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ImpactPanel({ analysis, onFileClick }: { analysis: ImpactAnalysis; onFileClick?: (path: string) => void }) {
  return (
    <div className="space-y-4">
      <RiskBanner analysis={analysis} />
      {analysis.on_call && <OnCallCard expert={analysis.on_call} label="On-Call for This File" />}
      <CoChangeList coChanges={analysis.co_changes} onFileClick={onFileClick} />
      <ChangeFrequencyChart frequency={analysis.change_frequency} />
      <CompactExpertList experts={analysis.experts} />
    </div>
  );
}
