import { Loader2 } from 'lucide-react';

export function LoadingDots() {
  return (
    <div className="flex items-center gap-2 text-gray-400 py-4">
      <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
      <span className="text-sm">Searching codebase memory...</span>
    </div>
  );
}

export function ThinkingIndicator({ message }: { message?: string }) {
  return (
    <div className="flex items-center gap-2 text-gray-400 py-4">
      <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
      <span className="text-sm">{message || 'Searching codebase memory...'}</span>
    </div>
  );
}

export function LoadingSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-3 animate-pulse py-4">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 bg-gray-800 rounded"
          style={{ width: `${85 - i * 15}%` }}
        />
      ))}
    </div>
  );
}
