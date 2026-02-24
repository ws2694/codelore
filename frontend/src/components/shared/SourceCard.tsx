import { GitCommit, GitPullRequest, FileText, MessageSquare, Lightbulb } from 'lucide-react';
import type { TimelineEntry } from '../../lib/types';

const EVENT_CONFIG: Record<string, { icon: typeof GitCommit; label: string; color: string }> = {
  commit: { icon: GitCommit, label: 'Commit', color: 'text-green-400' },
  pr_opened: { icon: GitPullRequest, label: 'PR', color: 'text-blue-400' },
  review_comment: { icon: MessageSquare, label: 'Review', color: 'text-yellow-400' },
  review: { icon: MessageSquare, label: 'Review', color: 'text-yellow-400' },
  pr_event: { icon: GitPullRequest, label: 'PR Event', color: 'text-blue-400' },
  decision: { icon: Lightbulb, label: 'Decision', color: 'text-brand-400' },
  doc: { icon: FileText, label: 'Doc', color: 'text-cyan-400' },
};

export default function SourceCard({ entry }: { entry: TimelineEntry }) {
  const config = EVENT_CONFIG[entry.event_type] || EVENT_CONFIG.commit;
  const Icon = config.icon;

  return (
    <div className="glass-panel p-4 hover:border-gray-700 transition-colors">
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 ${config.color}`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${config.color} bg-gray-800`}>
              {config.label}
            </span>
            <span className="text-xs text-gray-500">
              {entry.date ? new Date(entry.date).toLocaleDateString() : ''}
            </span>
            <span className="text-xs text-gray-500">@{entry.author}</span>
          </div>
          <p className="text-sm text-gray-200 font-medium truncate">{entry.title}</p>
          {entry.body && (
            <p className="text-xs text-gray-400 mt-1 line-clamp-2">{entry.body}</p>
          )}
          {entry.sha && (
            <code className="text-xs text-gray-500 mt-1 block">{entry.sha.slice(0, 8)}</code>
          )}
          {entry.pr_number && (
            <span className="text-xs text-blue-400 mt-1 block">PR #{entry.pr_number}</span>
          )}
        </div>
      </div>
    </div>
  );
}
