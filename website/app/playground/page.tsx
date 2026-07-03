'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Navbar } from '@/components/Navbar';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  orchestration?: OrchestrationData;
};

type OrchestrationData = {
  taskType: string;
  tier: string;
  models: { name: string; response: string; latency: number; correct: boolean }[];
  aggregator: string;
  consensus: number;
  qaScore: number;
  codeVerified: boolean;
  totalLatency: number;
  cost: string;
};

type Mode = 'quick' | 'fusion' | 'verify';

const EXAMPLE_PROMPTS = [
  'What is 9.9 vs 9.11 — which is larger?',
  'Write a Python function to merge two sorted lists',
  'Explain quantum entanglement in simple terms',
  'What is the derivative of x³ + 2x² - 5x + 1?',
];

const MODELS = [
  { id: 'glm-5.2', name: 'GLM-5.2', role: 'Orchestrator', context: '1M', capabilities: ['Tools', 'Thinking'] },
  { id: 'deepseek-v4-pro', name: 'DeepSeek V4 Pro', role: 'Reasoning', context: '1.6T', capabilities: ['Coding', 'Math', 'Reasoning'] },
  { id: 'kimi-k2.6', name: 'Kimi K2.6', role: 'Long Context', context: '262K', capabilities: ['Vision', 'Tools'] },
  { id: 'minimax-m3', name: 'MiniMax M3', role: 'Generation', context: '1M', capabilities: ['Vision', 'Creative'] },
  { id: 'nemotron-3-ultra', name: 'Nemotron 3 Ultra', role: 'Verifier', context: '1M', capabilities: ['Evaluation'] },
  { id: 'gpt-oss-120b', name: 'GPT-OSS 120B', role: 'Cheap Route', context: '131K', capabilities: ['Fast', 'Low cost'] },
];

const FREE_QUERY_LIMIT = 3;

export default function PlaygroundPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<Mode>('quick');
  const [selectedModels, setSelectedModels] = useState<string[]>(['glm-5.2', 'deepseek-v4-pro', 'kimi-k2.6']);
  const [temperature, setTemperature] = useState(0.7);
  const [status, setStatus] = useState<'ready' | 'submitted' | 'streaming' | 'error'>('ready');
  const [showOrchestration, setShowOrchestration] = useState<string | null>(null);
  const [freeQueriesUsed, setFreeQueriesUsed] = useState(0);
  const [showSignupPrompt, setShowSignupPrompt] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load free query count from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('timuclaude_free_queries');
    if (stored) setFreeQueriesUsed(parseInt(stored, 10));
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || status === 'submitted' || status === 'streaming') return;

    // Check free query limit
    if (freeQueriesUsed >= FREE_QUERY_LIMIT) {
      setShowSignupPrompt(true);
      return;
    }

    const userMessage: Message = { role: 'user', content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setStatus('submitted');

    // Increment free query counter
    const newCount = freeQueriesUsed + 1;
    setFreeQueriesUsed(newCount);
    localStorage.setItem('timuclaude_free_queries', newCount.toString());

    try {
      // Call the Timuclaude API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          mode,
          models: selectedModels,
          temperature,
        }),
        signal: abortControllerRef.current?.signal,
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      setStatus('streaming');

      // Read SSE stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';
      let orchestrationData: OrchestrationData | undefined;

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value, { stream: true });
          const lines = text.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ') && line !== 'data: [DONE]') {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.chunk) {
                  assistantContent += data.chunk;
                  setMessages((prev) => {
                    const updated = [...prev];
                    const lastAssistant = updated.findIndex((m) => m.role === 'assistant' && m.content === '');
                    if (lastAssistant >= 0) {
                      updated[lastAssistant] = { role: 'assistant', content: assistantContent };
                    } else {
                      updated.push({ role: 'assistant', content: assistantContent });
                    }
                    return updated;
                  });
                }
                if (data.orchestration) {
                  orchestrationData = data.orchestration;
                }
              } catch {
                // Ignore parse errors for partial chunks
              }
            }
          }
        }
      }

      // Add orchestration data to the last message
      if (orchestrationData) {
        setMessages((prev) => {
          const updated = [...prev];
          const lastAssistant = updated.findIndex((m) => m.role === 'assistant');
          if (lastAssistant >= 0) {
            updated[lastAssistant] = { ...updated[lastAssistant], orchestration: orchestrationData };
          }
          return updated;
        });
      }

      setStatus('ready');
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setStatus('ready');
      } else {
        setStatus('error');
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'Something went wrong. Please try again.',
          },
        ]);
      }
    }
  }, [input, status, messages, mode, selectedModels, temperature, freeQueriesUsed]);

  const handleStop = () => {
    abortControllerRef.current?.abort();
    setStatus('ready');
  };

  const toggleModel = (modelId: string) => {
    setSelectedModels((prev) =>
      prev.includes(modelId) ? prev.filter((m) => m !== modelId) : [...prev, modelId]
    );
  };

  const remainingFreeQueries = FREE_QUERY_LIMIT - freeQueriesUsed;

  return (
    <>
      <Navbar />
      <div className="flex h-screen pt-16">
        {/* Sidebar */}
        <aside
          className={`${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } md:translate-x-0 fixed md:sticky top-16 left-0 z-30 w-72 h-[calc(100vh-4rem)] bg-bg-secondary border-r border-border-subtle overflow-y-auto transition-transform duration-250 ease-spring`}
          aria-label="Playground settings"
        >
          <div className="p-4 space-y-6">
            {/* New Chat */}
            <button
              className="btn-primary w-full"
              onClick={() => {
                setMessages([]);
                setShowOrchestration(null);
              }}
            >
              New Chat
            </button>

            {/* Free Query Counter */}
            <div className="text-center">
              <div
                className={`badge ${remainingFreeQueries > 1 ? 'badge-olive' : remainingFreeQueries === 1 ? 'bg-accent-amber/12 text-accent-amber' : 'bg-accent-fig/12 text-accent-fig'}`}
              >
                {remainingFreeQueries} of {FREE_QUERY_LIMIT} free queries left
              </div>
            </div>

            {/* Mode Selector */}
            <div>
              <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">Mode</h3>
              <div className="space-y-1">
                {[
                  { id: 'quick' as Mode, label: 'Quick', desc: 'Single model, fast' },
                  { id: 'fusion' as Mode, label: 'Fusion', desc: '3-5 models in parallel' },
                  { id: 'verify' as Mode, label: 'Verify', desc: 'Fusion + code check + QA' },
                ].map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setMode(m.id)}
                    className={`w-full text-left p-2.5 rounded-sm transition-colors ${
                      mode === m.id
                        ? 'bg-accent-primary/10 text-text-primary border border-accent-primary/30'
                        : 'text-text-secondary hover:bg-bg-tertiary border border-transparent'
                    }`}
                  >
                    <div className="text-sm font-medium">{m.label}</div>
                    <div className="text-xs text-text-muted">{m.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Model Selector */}
            <div>
              <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">
                Models {mode === 'quick' ? '(select one)' : '(select 3-5)'}
              </h3>
              <div className="space-y-1">
                {MODELS.map((model) => (
                  <label
                    key={model.id}
                    className={`flex items-center gap-2 p-2 rounded-sm cursor-pointer transition-colors ${
                      selectedModels.includes(model.id) ? 'bg-bg-tertiary' : 'hover:bg-bg-tertiary'
                    }`}
                  >
                    <input
                      type={mode === 'quick' ? 'radio' : 'checkbox'}
                      checked={selectedModels.includes(model.id)}
                      onChange={() => {
                        if (mode === 'quick') {
                          setSelectedModels([model.id]);
                        } else {
                          toggleModel(model.id);
                        }
                      }}
                      className="accent-accent-primary"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-text-primary truncate">{model.name}</div>
                      <div className="text-xs text-text-muted truncate">{model.role}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Advanced */}
            <div>
              <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">Advanced</h3>
              <div className="space-y-3">
                <div>
                  <label className="flex items-center justify-between text-sm text-text-secondary mb-1">
                    <span>Temperature</span>
                    <span className="font-mono text-text-primary">{temperature.toFixed(1)}</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full accent-accent-primary"
                    aria-label="Temperature"
                  />
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* Sidebar backdrop (mobile) */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-black/30 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Chat Area */}
        <main
          className="flex-1 flex flex-col h-[calc(100vh-4rem)]"
          aria-label="Timuclaude Playground"
          id="main-content"
        >
          {/* Mobile sidebar toggle */}
          <button
            className="md:hidden absolute top-20 left-4 z-10 p-2 bg-bg-secondary rounded-sm border border-border-subtle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle settings"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1A1816" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 md:px-6 py-6">
            <div className="max-w-3xl mx-auto space-y-6">
              {/* Empty State */}
              {messages.length === 0 && (
                <div className="text-center pt-12">
                  <h2 className="text-2xl font-semibold text-text-primary mb-2">
                    Ask Timuclaude anything
                  </h2>
                  <p className="text-text-secondary mb-8">
                    5 AI models are ready to collaborate on your question.
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {EXAMPLE_PROMPTS.map((prompt, i) => (
                      <button
                        key={i}
                        onClick={() => setInput(prompt)}
                        className="badge-muted hover:bg-bg-tertiary hover:text-text-primary transition-colors cursor-pointer"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Messages */}
              {messages.map((message, i) => (
                <div
                  key={i}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] ${
                      message.role === 'user'
                        ? 'bg-bg-dark text-text-inverse rounded-md rounded-tr-sm'
                        : 'bg-white border border-border-subtle rounded-md rounded-tl-sm'
                    } p-4`}
                  >
                    <div
                      className={`whitespace-pre-wrap text-sm leading-relaxed ${
                        message.role === 'user' ? 'text-text-inverse' : 'text-text-primary'
                      }`}
                      role={message.role === 'assistant' ? 'status' : undefined}
                      aria-live={message.role === 'assistant' ? 'polite' : undefined}
                      aria-atomic="false"
                    >
                      {message.content}
                      {status === 'streaming' && i === messages.length - 1 && message.role === 'assistant' && (
                        <span className="inline-block w-2 h-4 bg-accent-primary ml-0.5 animate-blink" />
                      )}
                    </div>

                    {/* Orchestration summary bar */}
                    {message.orchestration && message.role === 'assistant' && (
                      <div className="mt-3 pt-3 border-t border-border-subtle">
                        <button
                          onClick={() => setShowOrchestration(showOrchestration === String(i) ? null : String(i))}
                          className="flex items-center gap-2 text-xs text-text-muted hover:text-text-primary transition-colors"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                            <path d="M12 6v6l4 2" />
                          </svg>
                          {message.orchestration.models.length} models · {message.orchestration.totalLatency}s · {message.orchestration.cost}
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ transform: showOrchestration === String(i) ? 'rotate(180deg)' : 'none', transition: 'transform 150ms' }}>
                            <polyline points="6 9 12 15 18 9" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Typing indicator */}
              {status === 'submitted' && (
                <div className="flex justify-start">
                  <div className="bg-white border border-border-subtle rounded-md rounded-tl-sm p-4">
                    <div className="flex gap-1">
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                    </div>
                  </div>
                </div>
              )}

              {/* Error state */}
              {status === 'error' && (
                <div className="flex justify-center">
                  <div className="bg-accent-fig/8 border border-accent-fig/20 rounded-md p-4 text-sm text-text-secondary text-center">
                    Something went wrong.{' '}
                    <button onClick={handleSend} className="text-accent-primary hover:underline">
                      Try again
                    </button>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Orchestration Detail Panel */}
          {showOrchestration && messages[parseInt(showOrchestration)]?.orchestration && (
            <OrchestrationPanel
              data={messages[parseInt(showOrchestration)].orchestration!}
              onClose={() => setShowOrchestration(null)}
            />
          )}

          {/* Signup Prompt */}
          {showSignupPrompt && (
            <div
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
              onClick={() => setShowSignupPrompt(false)}
            >
              <div className="absolute inset-0 bg-black/30" />
              <div
                className="relative bg-bg-primary rounded-md p-6 max-w-sm w-full text-center"
                onClick={(e) => e.stopPropagation()}
                role="alertdialog"
                aria-modal="true"
                aria-labelledby="signup-title"
                aria-describedby="signup-desc"
              >
                <h2 id="signup-title" className="text-lg font-semibold text-text-primary mb-2">
                  You've used all {FREE_QUERY_LIMIT} free queries!
                </h2>
                <p id="signup-desc" className="text-sm text-text-secondary mb-6">
                  Create a free account for more queries, or explore the playground features.
                </p>
                <div className="space-y-2">
                  <button className="btn-primary w-full">Create Free Account</button>
                  <button className="btn-secondary w-full">Maybe Later</button>
                </div>
              </div>
            </div>
          )}

          {/* Input Bar */}
          <div className="border-t border-border-subtle bg-bg-primary p-4">
            <div className="max-w-3xl mx-auto">
              <div className="flex gap-2 items-end">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ask Timuclaude anything..."
                  rows={1}
                  className="input flex-1 resize-none min-h-[44px] max-h-32"
                  aria-label="Enter your question"
                  disabled={status === 'submitted' || status === 'streaming'}
                />
                {status === 'submitted' || status === 'streaming' ? (
                  <button
                    onClick={handleStop}
                    className="btn-secondary !px-3"
                    aria-label="Stop generating"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
                  </button>
                ) : (
                  <button
                    onClick={handleSend}
                    disabled={!input.trim()}
                    className="btn-accent !px-3 disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="Send message"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                    </svg>
                  </button>
                )}
              </div>
              <p className="text-xs text-text-muted mt-2 text-center">
                Timuclaude orchestrates multiple AI models for superior answers · Free for first {FREE_QUERY_LIMIT} queries
              </p>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}

function OrchestrationPanel({ data, onClose }: { data: OrchestrationData; onClose: () => void }) {
  return (
    <div className="border-t border-border-subtle bg-bg-secondary max-h-[40vh] overflow-y-auto">
      <div className="max-w-3xl mx-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-text-primary">How this answer was built</h3>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary" aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {/* Classification */}
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-accent-olive/20 flex items-center justify-center flex-shrink-0">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
            </div>
            <div>
              <div className="text-sm font-medium text-text-primary">Understanding your question</div>
              <div className="text-xs text-text-muted">Classified as: {data.taskType} · Routed to: {data.tier} tier</div>
            </div>
          </div>

          {/* Model responses */}
          {data.models.length > 1 && (
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-accent-primary/20 flex items-center justify-center flex-shrink-0">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#D97757" strokeWidth="2"><circle cx="12" cy="12" r="3" /></svg>
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-text-primary mb-2">Combining multiple answers ({data.models.length} models)</div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  {data.models.map((model, i) => (
                    <div key={i} className="bg-white border border-border-subtle rounded-sm p-2">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-text-primary">{model.name}</span>
                        <span className={`text-xs ${model.correct ? 'text-accent-olive' : 'text-accent-fig'}`}>
                          {model.correct ? '✓' : '✗'}
                        </span>
                      </div>
                      <p className="text-xs text-text-muted line-clamp-2">{model.response}</p>
                      <div className="text-xs text-text-muted mt-1">{model.latency}s</div>
                    </div>
                  ))}
                </div>
                <div className="text-xs text-text-muted mt-2">
                  Aggregated by: {data.aggregator} · Consensus: {data.consensus}/3 agree
                </div>
              </div>
            </div>
          )}

          {/* Code verification */}
          {data.codeVerified && (
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-accent-olive/20 flex items-center justify-center flex-shrink-0">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
              </div>
              <div>
                <div className="text-sm font-medium text-text-primary">Code verification</div>
                <div className="text-xs text-text-muted">✓ Verified — code output matches the answer</div>
              </div>
            </div>
          )}

          {/* Self-QA */}
          {data.qaScore > 0 && (
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-accent-olive/20 flex items-center justify-center flex-shrink-0">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
              </div>
              <div>
                <div className="text-sm font-medium text-text-primary">Quality check</div>
                <div className="text-xs text-text-muted">Self-QA score: {data.qaScore}/10 · {data.qaScore >= 8 ? '✓ Passed' : '⚠ Below threshold'}</div>
              </div>
            </div>
          )}

          {/* Summary */}
          <div className="flex items-center gap-4 pt-2 border-t border-border-subtle text-xs text-text-muted">
            <span>Total: {data.totalLatency}s</span>
            <span>·</span>
            <span>Cost: {data.cost}</span>
            <span>·</span>
            <span>{data.models.length} model{data.models.length > 1 ? 's' : ''}</span>
          </div>
        </div>
      </div>
    </div>
  );
}