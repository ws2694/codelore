import { useRef, useEffect } from 'react';
import { Brain, RotateCcw, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useChat } from '../../hooks/useChat';
import ChatInput from '../shared/ChatInput';
import { LoadingDots } from '../shared/LoadingState';

const SAMPLE_QUESTIONS = [
  'Why does the auth service use Redis instead of Postgres?',
  'What were the key architectural decisions in the last 3 months?',
  'Who are the domain experts for the payments module?',
  'How has the webhook handler evolved over time?',
  'Why did we choose GraphQL over REST for the client API?',
];

export default function AskMode() {
  const { messages, isLoading, error, sendMessage, clearChat } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800/50 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Brain className="w-5 h-5 text-brand-400" />
          <div>
            <h2 className="font-semibold text-white">Ask CodeLore</h2>
            <p className="text-xs text-gray-500">Ask anything about your codebase's history and decisions</p>
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            New conversation
          </button>
        )}
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full max-w-lg mx-auto text-center">
            <div className="w-16 h-16 rounded-2xl bg-brand-600/20 border border-brand-500/30 flex items-center justify-center mb-6">
              <Sparkles className="w-8 h-8 text-brand-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              What would you like to know?
            </h3>
            <p className="text-sm text-gray-400 mb-8">
              Ask about design decisions, code history, architecture rationale, or anything else about your codebase.
            </p>
            <div className="grid gap-2 w-full">
              {SAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-left text-sm text-gray-300 px-4 py-3 rounded-lg bg-gray-800/50 hover:bg-gray-800 border border-gray-800 hover:border-gray-700 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-brand-600/30 border border-brand-500/30 text-gray-100'
                      : 'glass-panel text-gray-200'
                  }`}
                >
                  {msg.role === 'assistant' ? (
                    <div className="markdown-body text-sm">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-sm">{msg.content}</p>
                  )}
                </div>
              </div>
            ))}
            {isLoading && <LoadingDots />}
            {error && (
              <div className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
                {error}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-gray-800/50 shrink-0">
        <div className="max-w-3xl mx-auto">
          <ChatInput
            onSend={(msg) => sendMessage(msg)}
            isLoading={isLoading}
            placeholder="Ask about design decisions, architecture rationale, code history..."
          />
        </div>
      </div>
    </div>
  );
}
