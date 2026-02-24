import { Lightbulb, User, Calendar, Tag, FileCode, ArrowRight } from 'lucide-react';
import type { Decision } from '../../lib/types';

export default function DecisionGraph({ decisions }: { decisions: Decision[] }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm text-gray-400">{decisions.length} architectural decisions</h3>
      </div>

      {decisions.map((d) => (
        <DecisionCard key={d.decision_id} decision={d} />
      ))}
    </div>
  );
}

function DecisionCard({ decision: d }: { decision: Decision }) {
  const importanceColor =
    d.importance >= 4 ? 'text-red-400 bg-red-400/10 border-red-400/30' :
    d.importance >= 3 ? 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30' :
    'text-green-400 bg-green-400/10 border-green-400/30';

  return (
    <div className="glass-panel p-5 hover:border-gray-700 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 w-8 h-8 rounded-lg bg-brand-500/10 border border-brand-500/30 flex items-center justify-center shrink-0">
            <Lightbulb className="w-4 h-4 text-brand-400" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">{d.title}</h4>
            <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <User className="w-3 h-3" />
                @{d.decided_by}
              </span>
              {d.decided_at && (
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {new Date(d.decided_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
        </div>
        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${importanceColor} shrink-0`}>
          Impact: {d.importance.toFixed(1)}
        </span>
      </div>

      {/* Summary */}
      <p className="text-sm text-gray-300 mb-3 leading-relaxed">{d.summary}</p>

      {/* Rationale */}
      {d.rationale && (
        <div className="mb-3 bg-gray-800/30 rounded-lg p-3">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-medium">Rationale</p>
          <p className="text-xs text-gray-400 leading-relaxed">{d.rationale}</p>
        </div>
      )}

      {/* Alternatives */}
      {d.alternatives_considered && (
        <div className="mb-3">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-medium">Alternatives Considered</p>
          <p className="text-xs text-gray-400 leading-relaxed">{d.alternatives_considered}</p>
        </div>
      )}

      {/* Footer: tags + files */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        {d.tags && d.tags.length > 0 && (
          <div className="flex items-center gap-1 flex-wrap">
            <Tag className="w-3 h-3 text-gray-600" />
            {d.tags.map((tag) => (
              <span key={tag} className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded">
                {tag}
              </span>
            ))}
          </div>
        )}
        {d.affected_files && d.affected_files.length > 0 && (
          <div className="flex items-center gap-1 flex-wrap">
            <FileCode className="w-3 h-3 text-gray-600" />
            {d.affected_files.slice(0, 3).map((f) => (
              <code key={f} className="text-[10px] text-gray-500 font-mono">{f}</code>
            ))}
            {d.affected_files.length > 3 && (
              <span className="text-[10px] text-gray-600">+{d.affected_files.length - 3}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
