import { GitCommit, GitPullRequest, MessageSquare, Lightbulb } from 'lucide-react';
import type { TimelineEntry } from '../../lib/types';

const EVENT_STYLES: Record<string, { icon: typeof GitCommit; color: string; bg: string; border: string }> = {
  commit: { icon: GitCommit, color: 'text-green-400', bg: 'bg-green-400/10', border: 'border-green-400/30' },
  pr_opened: { icon: GitPullRequest, color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400/30' },
  review_comment: { icon: MessageSquare, color: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/30' },
  review: { icon: MessageSquare, color: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/30' },
  pr_event: { icon: GitPullRequest, color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400/30' },
  decision: { icon: Lightbulb, color: 'text-brand-400', bg: 'bg-brand-400/10', border: 'border-brand-400/30' },
};

export default function Timeline({ entries }: { entries: TimelineEntry[] }) {
  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-[18px] top-2 bottom-2 w-px bg-gray-800" />

      <div className="space-y-1">
        {entries.map((entry, i) => {
          const style = EVENT_STYLES[entry.event_type] || EVENT_STYLES.commit;
          const Icon = style.icon;
          const date = entry.date ? new Date(entry.date) : null;

          return (
            <div key={`${entry.sha || entry.pr_number || i}-${i}`} className="relative flex gap-4 group">
              {/* Dot on the timeline */}
              <div className={`relative z-10 w-9 h-9 rounded-full ${style.bg} border ${style.border} flex items-center justify-center shrink-0`}>
                <Icon className={`w-4 h-4 ${style.color}`} />
              </div>

              {/* Content card */}
              <div className="flex-1 glass-panel p-4 mb-2 group-hover:border-gray-700 transition-colors">
                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                  {date && (
                    <span className="text-xs text-gray-500 font-mono">
                      {date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                    </span>
                  )}
                  <span className="text-xs text-gray-600">|</span>
                  <span className="text-xs text-gray-400">@{entry.author}</span>
                  {entry.sha && (
                    <>
                      <span className="text-xs text-gray-600">|</span>
                      <code className="text-xs text-green-400/70">{entry.sha.slice(0, 8)}</code>
                    </>
                  )}
                  {entry.pr_number && (
                    <>
                      <span className="text-xs text-gray-600">|</span>
                      <span className="text-xs text-blue-400">PR #{entry.pr_number}</span>
                    </>
                  )}
                </div>

                <h4 className="text-sm font-medium text-gray-200 mb-1">{entry.title}</h4>

                {entry.body && entry.body !== entry.title && (
                  <p className="text-xs text-gray-400 leading-relaxed whitespace-pre-wrap line-clamp-4">
                    {entry.body}
                  </p>
                )}

                {entry.files && entry.files.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {entry.files.slice(0, 5).map((f) => (
                      <span key={f} className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded font-mono">
                        {f}
                      </span>
                    ))}
                    {entry.files.length > 5 && (
                      <span className="text-[10px] text-gray-500">+{entry.files.length - 5} more</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
