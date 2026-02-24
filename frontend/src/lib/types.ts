export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: ToolCall[];
}

export interface ToolCall {
  tool: string;
  params: Record<string, unknown>;
}

export interface TimelineEntry {
  date: string;
  sha?: string;
  pr_number?: number;
  title: string;
  author: string;
  event_type: 'commit' | 'pr_opened' | 'review_comment' | 'review' | 'pr_event' | 'decision';
  body?: string;
  files?: string[];
}

export interface Decision {
  decision_id: string;
  title: string;
  summary: string;
  rationale: string;
  alternatives_considered?: string;
  decided_by: string;
  decided_at: string;
  status: string;
  tags: string[];
  affected_files: string[];
  affected_modules: string[];
  importance: number;
}

export interface OnboardStep {
  step: number;
  content: string;
  conversation_id: string;
}

export interface HealthStatus {
  status: string;
  elasticsearch: boolean;
  indices: Record<string, number>;
}

export interface Expert {
  author: string;
  commits: number;
  last_active: string;
  first_commit?: string;
  recent_commits?: number;
}

export interface ExpertFinderResult {
  module: string;
  experts: Expert[];
  on_call: Expert | null;
  bus_factor: number;
  total_commits: number;
}

export interface SemanticSearchResult {
  index: string;
  score: number;
  title: string;
  summary: string;
  author: string;
  date: string;
  metadata: Record<string, unknown>;
}

export interface CoChange {
  path: string;
  shared_commits: number;
  coupling_ratio: number;
}

export interface RiskLevel {
  level: 'low' | 'medium' | 'high';
  score: number;
  factors: string[];
}

export interface ChangeFrequency {
  month: string;
  count: number;
}

export interface ImpactAnalysis {
  filepath: string;
  total_commits: number;
  bus_factor: number;
  latest_change: string | null;
  risk_level: RiskLevel;
  change_frequency: ChangeFrequency[];
  co_changes: CoChange[];
  experts: Expert[];
  on_call: Expert | null;
}

export type Mode = 'ask' | 'onboard' | 'explore';

// SSE streaming types
export interface SSEStatusEvent {
  phase: 'thinking' | 'streaming';
  message: string;
}

export interface SSEChunkEvent {
  text: string;
}

export interface SSEMetadataEvent {
  conversation_id?: string;
  step?: number;
  sources?: ToolCall[];
}

export interface SSEErrorEvent {
  message: string;
  code: number;
}

export type SSEEventHandler = {
  onStatus?: (data: SSEStatusEvent) => void;
  onChunk?: (data: SSEChunkEvent) => void;
  onMetadata?: (data: SSEMetadataEvent) => void;
  onDone?: () => void;
  onError?: (data: SSEErrorEvent) => void;
};

export interface AuthStatus {
  authenticated: boolean;
  method: 'oauth' | 'env' | null;
  user: string | null;
  avatar_url: string | null;
  selected_repo: string | null;
  oauth_configured: boolean;
}

export interface GitHubRepo {
  full_name: string;
  name: string;
  owner: string;
  description: string;
  language: string;
  stars: number;
  updated_at: string;
  private: boolean;
}
