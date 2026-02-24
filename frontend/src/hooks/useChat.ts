import { useState, useCallback, useRef } from 'react';
import { chatStreamApi } from '../lib/api';
import type { ChatMessage, SSEEventHandler, SSEStatusEvent, ToolCall } from '../lib/types';

let msgCounter = 0;

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (question: string, mode = 'ask') => {
    setError(null);
    setIsLoading(true);
    setIsStreaming(false);
    setStatusMessage('Searching codebase memory...');

    const userMsg: ChatMessage = {
      id: `msg-${++msgCounter}`,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    const assistantMsgId = `msg-${++msgCounter}`;
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);

    const controller = new AbortController();
    abortRef.current = controller;
    let accumulated = '';

    const handlers: SSEEventHandler = {
      onStatus: (data: SSEStatusEvent) => {
        if (data.phase === 'thinking') {
          setIsLoading(true);
          setIsStreaming(false);
          setStatusMessage(data.message);
        } else if (data.phase === 'streaming') {
          setIsLoading(false);
          setIsStreaming(true);
          setStatusMessage('');
        }
      },
      onChunk: (data) => {
        accumulated += data.text;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId ? { ...msg, content: accumulated } : msg,
          ),
        );
      },
      onMetadata: (data) => {
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
        }
        if (data.sources) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? { ...msg, sources: data.sources as ToolCall[] }
                : msg,
            ),
          );
        }
      },
      onDone: () => {
        setIsLoading(false);
        setIsStreaming(false);
      },
      onError: (data) => {
        setIsLoading(false);
        setIsStreaming(false);
        setError(data.message);
        if (!accumulated) {
          setMessages((prev) => prev.filter((msg) => msg.id !== assistantMsgId));
        }
      },
    };

    try {
      await chatStreamApi.ask(question, handlers, conversationId, mode, controller.signal);
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      const message = err instanceof Error ? err.message : 'Failed to get response';
      setError(message);
      setIsLoading(false);
      setIsStreaming(false);
    }
  }, [conversationId]);

  const clearChat = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setConversationId(undefined);
    setError(null);
    setIsLoading(false);
    setIsStreaming(false);
  }, []);

  return { messages, isLoading, isStreaming, statusMessage, error, sendMessage, clearChat, conversationId };
}
