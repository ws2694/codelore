import axios from 'axios';
import type { HealthStatus, TimelineEntry, Decision, Expert, OnboardStep } from './types';

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
