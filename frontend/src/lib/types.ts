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
}

export type Mode = 'ask' | 'onboard' | 'explore';
