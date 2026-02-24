import { GitCommit, GitPullRequest, FileText, MessageSquare, Lightbulb, Sparkles } from 'lucide-react';
import type { SemanticSearchResult } from '../../lib/types';

const INDEX_STYLES: Record<string, { icon: typeof GitCommit; color: string; bg: string; border: string; label: string }> = {
  commits:      { icon: GitCommit,      color: 'text-green-400',  bg: 'bg-green-400/10',  border: 'border-green-400/30',  label: 'Commit' },
  'pr-events':  { icon: GitPullRequest, color: 'text-blue-400',   bg: 'bg-blue-400/10',   border: 'border-blue-400/30',   label: 'PR' },
  docs:         { icon: FileText,       color: 'text-cyan-400',   bg: 'bg-cyan-400/10',   border: 'border-cyan-400/30',   label: 'Doc' },
  slack:        { icon: MessageSquare,  color: 'text-yellow-400', bg: 'bg-yellow-400/10',  border: 'border-yellow-400/30', label: 'Slack' },
  decisions:    { icon: Lightbulb,      color: 'text-brand-400',  bg: 'bg-brand-400/10',   border: 'border-brand-400/30',  label: 'Decision' },
};

export default function SemanticResults({ results }: { results: SemanticSearchResult[] }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm text-gray-400">{results.length} semantic matches</h3>
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <Sparkles className="w-3 h-3" />
          Ranked by vector similarity
        </div>
      </div>

      {results.map((r, i) => {
        const style = INDEX_STYLES[r.index] || INDEX_STYLES.commits;
        const Icon = style.icon;
        const date = r.date ? new Date(r.date) : null;
        const scorePercent = Math.round(r.score * 100);

        return (
          <div key={`${r.index}-${i}`} className="glass-panel p-4 hover:border-gray-700 transition-colors">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-start gap-3">
                <div className={`w-8 h-8 rounded-lg ${style.bg} border ${style.border} flex items-center justify-center shrink-0`}>
                  <Icon className={`w-4 h-4 ${style.color}`} />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-200">{r.title || 'Untitled'}</h4>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${style.bg} ${style.color} border ${style.border}`}>
                      {style.label}
                    </span>
                    {r.author && r.author !== 'unknown' && <span>@{r.author}</span>}
                    {date && (
                      <span>{date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <div className="w-12 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-brand-500 rounded-full"
                    style={{ width: `${scorePercent}%` }}
                  />
                </div>
                <span className="text-[10px] text-gray-500 font-mono w-8 text-right">{scorePercent}%</span>
              </div>
            </div>

            {r.summary && (
              <p className="text-xs text-gray-400 leading-relaxed line-clamp-3 ml-11">
                {r.summary}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
