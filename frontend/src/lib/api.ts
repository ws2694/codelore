import axios from 'axios';
import type { HealthStatus, TimelineEntry, Decision, Expert, OnboardStep, AuthStatus, GitHubRepo, SSEEventHandler } from './types';

const api = axios.create({ baseURL: '/api' });

export const chatApi = {
  ask: async (question: string, conversationId?: string, mode = 'ask') => {
    const { data } = await api.post('/chat/ask', {
      question,
      conversation_id: conversationId,
      mode,
    });
    return data as {
      answer: string;
      conversation_id: string;
      sources: { tool: string; params: Record<string, unknown> }[];
    };
  },
};

export const exploreApi = {
  getTimeline: async (filepath: string) => {
    const { data } = await api.get(`/explore/timeline/${encodeURIComponent(filepath)}`);
    return data as { filepath: string; entries: TimelineEntry[]; total: number };
  },

  getDecisions: async (query?: string) => {
    const { data } = await api.get('/explore/decisions', { params: { query } });
    return data as { decisions: Decision[]; total: number };
  },

  getExperts: async (module: string) => {
    const { data } = await api.get(`/explore/experts/${encodeURIComponent(module)}`);
    return data as { module: string; experts: Expert[] };
  },
};

export const onboardApi = {
  start: async (module?: string, topic?: string) => {
    const { data } = await api.post('/onboard/start', null, {
      params: { module, topic },
    });
    return data as OnboardStep;
  },

  next: async (conversationId: string, currentStep: number) => {
    const { data } = await api.post('/onboard/next', null, {
      params: { conversation_id: conversationId, current_step: currentStep },
    });
    return data as OnboardStep;
  },
};

export const ingestApi = {
  trigger: async (repo?: string) => {
    const { data } = await api.post('/ingest/repo', null, {
      params: { repo },
    });
    return data;
  },

  status: async () => {
    const { data } = await api.get('/ingest/status');
    return data;
  },
};

export const healthApi = {
  check: async () => {
    const { data } = await api.get('/health');
    return data as HealthStatus;
  },
};

export const authApi = {
  getGitHubUrl: async () => {
    const { data } = await api.get('/auth/github/url');
    return data as { url: string };
  },

  callback: async (code: string) => {
    const { data } = await api.get('/auth/github/callback', { params: { code } });
    return data as { authenticated: boolean; user: string; avatar_url: string; name: string };
  },

  status: async () => {
    const { data } = await api.get('/auth/status');
    return data as AuthStatus;
  },

  logout: async () => {
    const { data } = await api.post('/auth/logout');
    return data;
  },

  selectRepo: async (repo: string) => {
    const { data } = await api.post('/auth/select-repo', null, { params: { repo } });
    return data;
  },
};

export const githubApi = {
  listRepos: async (page = 1, perPage = 30) => {
    const { data } = await api.get('/github/repos', {
      params: { page, per_page: perPage },
    });
    return data as { repos: GitHubRepo[]; page: number; per_page: number };
  },
};

// ── SSE streaming ───────────────────────────────────────────────────────

async function fetchSSE(
  url: string,
  body: Record<string, unknown> | null,
  params: Record<string, string | number | undefined>,
  handlers: SSEEventHandler,
  signal?: AbortSignal,
): Promise<void> {
  const queryParts: string[] = [];
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') {
      queryParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
    }
  }
  const qs = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';

  const response = await fetch(`/api${url}${qs}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });

  if (!response.ok) {
    const text = await response.text();
    handlers.onError?.({ message: text || `HTTP ${response.status}`, code: response.status });
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    handlers.onError?.({ message: 'No response body', code: 0 });
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';

      for (const part of parts) {
        if (!part.trim()) continue;

        let eventType = '';
        let eventData = '';

        for (const line of part.split('\n')) {
          if (line.startsWith('event: ')) eventType = line.slice(7).trim();
          else if (line.startsWith('data: ')) eventData = line.slice(6);
        }

        if (!eventType || !eventData) continue;

        try {
          const parsed = JSON.parse(eventData);
          switch (eventType) {
            case 'status':   handlers.onStatus?.(parsed); break;
            case 'chunk':    handlers.onChunk?.(parsed); break;
            case 'metadata': handlers.onMetadata?.(parsed); break;
            case 'done':     handlers.onDone?.(); break;
            case 'error':    handlers.onError?.(parsed); break;
          }
        } catch {
          // skip malformed JSON
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export const chatStreamApi = {
  ask: (
    question: string,
    handlers: SSEEventHandler,
    conversationId?: string,
    mode = 'ask',
    signal?: AbortSignal,
  ) =>
    fetchSSE(
      '/chat/ask/stream',
      { question, conversation_id: conversationId, mode },
      {},
      handlers,
      signal,
    ),
};

export const onboardStreamApi = {
  start: (
    handlers: SSEEventHandler,
    module?: string,
    topic?: string,
    signal?: AbortSignal,
  ) =>
    fetchSSE('/onboard/start/stream', null, { module, topic }, handlers, signal),

  next: (
    conversationId: string,
    currentStep: number,
    handlers: SSEEventHandler,
    signal?: AbortSignal,
  ) =>
    fetchSSE(
      '/onboard/next/stream',
      null,
      { conversation_id: conversationId, current_step: currentStep },
      handlers,
      signal,
    ),
};
