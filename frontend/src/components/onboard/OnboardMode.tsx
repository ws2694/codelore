import { useState } from 'react';
import { GraduationCap, ArrowRight, ArrowLeft, RotateCcw, BookOpen, Layers, Clock } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { onboardApi } from '../../lib/api';
import { LoadingDots } from '../shared/LoadingState';

const TOPICS = [
  { id: 'architecture', label: 'Architecture Overview', icon: Layers, desc: 'High-level system design and key modules' },
  { id: 'auth', label: 'Authentication', icon: BookOpen, desc: 'JWT, sessions, OAuth, and security decisions' },
  { id: 'payments', label: 'Payments', icon: BookOpen, desc: 'Stripe integration, webhooks, and billing' },
  { id: 'recent', label: 'Recent Changes', icon: Clock, desc: 'What changed in the last sprint' },
];

interface OnboardState {
  step: number;
  content: string;
  conversationId: string;
}

export default function OnboardMode() {
  const [started, setStarted] = useState(false);
  const [steps, setSteps] = useState<OnboardState[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTopic, setSelectedTopic] = useState('');

  const startOnboarding = async (topic: string) => {
    setIsLoading(true);
    setError(null);
    setSelectedTopic(topic);

    try {
      const isModule = !['architecture', 'recent'].includes(topic);
      const result = await onboardApi.start(
        isModule ? topic : undefined,
        isModule ? undefined : topic,
      );

      setSteps([{
        step: result.step,
        content: result.content,
        conversationId: result.conversation_id,
      }]);
      setCurrentIndex(0);
      setStarted(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to start onboarding');
    } finally {
      setIsLoading(false);
    }
  };

  const nextStep = async () => {
    const current = steps[currentIndex];
    if (!current) return;

    // If we already fetched the next step, just navigate
    if (currentIndex < steps.length - 1) {
      setCurrentIndex(currentIndex + 1);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await onboardApi.next(current.conversationId, current.step);
      setSteps((prev) => [...prev, {
        step: result.step,
        content: result.content,
        conversationId: result.conversation_id,
      }]);
      setCurrentIndex(steps.length);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load next step');
    } finally {
      setIsLoading(false);
    }
  };

  const prevStep = () => {
    if (currentIndex > 0) setCurrentIndex(currentIndex - 1);
  };

  const reset = () => {
    setStarted(false);
    setSteps([]);
    setCurrentIndex(0);
    setError(null);
    setSelectedTopic('');
  };

  const currentStep = steps[currentIndex];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800/50 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <GraduationCap className="w-5 h-5 text-brand-400" />
          <div>
            <h2 className="font-semibold text-white">
              {started ? `Onboarding: ${selectedTopic}` : 'Onboard'}
            </h2>
            <p className="text-xs text-gray-500">
              {started ? `Step ${currentIndex + 1} of ${steps.length}+` : 'Guided learning paths for your codebase'}
            </p>
          </div>
        </div>
        {started && (
          <button
            onClick={reset}
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            Start over
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {!started ? (
          /* Topic selection */
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <div className="w-16 h-16 rounded-2xl bg-brand-600/20 border border-brand-500/30 flex items-center justify-center mx-auto mb-4">
                <GraduationCap className="w-8 h-8 text-brand-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Choose a learning path</h3>
              <p className="text-sm text-gray-400">
                CodeLore will guide you through the key decisions and architecture of each area.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {TOPICS.map((topic) => {
                const Icon = topic.icon;
                return (
                  <button
                    key={topic.id}
                    onClick={() => startOnboarding(topic.id)}
                    disabled={isLoading}
                    className="glass-panel p-5 text-left hover:border-brand-500/30 transition-all group disabled:opacity-50"
                  >
                    <Icon className="w-5 h-5 text-brand-400 mb-3" />
                    <h4 className="text-sm font-medium text-white mb-1 group-hover:text-brand-300 transition-colors">
                      {topic.label}
                    </h4>
                    <p className="text-xs text-gray-500">{topic.desc}</p>
                  </button>
                );
              })}
            </div>

            {isLoading && (
              <div className="mt-6">
                <LoadingDots />
              </div>
            )}
            {error && (
              <div className="mt-4 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
                {error}
              </div>
            )}
          </div>
        ) : (
          /* Step content */
          <div className="max-w-3xl mx-auto">
            {/* Progress bar */}
            <div className="flex items-center gap-2 mb-6">
              {steps.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentIndex(i)}
                  className={`h-1.5 rounded-full flex-1 max-w-[60px] transition-colors ${
                    i === currentIndex
                      ? 'bg-brand-500'
                      : i < currentIndex
                      ? 'bg-brand-500/40'
                      : 'bg-gray-800'
                  }`}
                />
              ))}
              <div className="h-1.5 rounded-full flex-1 max-w-[60px] bg-gray-800/50" />
            </div>

            {/* Step content */}
            {currentStep && (
              <div className="glass-panel p-6">
                <div className="markdown-body text-sm">
                  <ReactMarkdown>{currentStep.content}</ReactMarkdown>
                </div>
              </div>
            )}

            {isLoading && (
              <div className="mt-4">
                <LoadingDots />
              </div>
            )}
            {error && (
              <div className="mt-4 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
                {error}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Navigation footer */}
      {started && (
        <div className="px-6 py-4 border-t border-gray-800/50 shrink-0">
          <div className="max-w-3xl mx-auto flex items-center justify-between">
            <button
              onClick={prevStep}
              disabled={currentIndex === 0}
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 disabled:opacity-30 disabled:cursor-not-allowed px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Previous
            </button>
            <span className="text-xs text-gray-500">Step {currentIndex + 1}</span>
            <button
              onClick={nextStep}
              disabled={isLoading}
              className="flex items-center gap-2 text-sm text-white bg-brand-600 hover:bg-brand-500 disabled:opacity-50 px-4 py-2 rounded-lg transition-colors"
            >
              Continue
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
