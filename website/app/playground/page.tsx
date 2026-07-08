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

const EXAMPLE_PROMPTS = [
  'What is 9.9 vs 9.11 — which is larger?',
  'Write a Python function to merge two sorted lists',
  'Explain quantum entanglement in simple terms',
  'What is the derivative of x³ + 2x² - 5x + 1?',
];

export default function PlaygroundPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState<'ready' | 'submitted' | 'streaming' | 'error'>('ready');
  const [showOrchestration, setShowOrchestration] = useState<string | null>(null);
  const [freeQueriesUsed, setFreeQueriesUsed] = useState(0);
  const [limitMessage, setLimitMessage] = useState<string | null>(null);
  const [showUpgradeBanner, setShowUpgradeBanner] = useState(false);
  const [showQuickStart, setShowQuickStart] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  // Index of the assistant message currently being streamed — avoids
  // creating a new message bubble on every chunk (the old code searched
  // for an assistant with content === '' which never existed, so every
  // chunk pushed a new message and the response repeated N times).
  const streamingIdxRef = useRef<number>(-1);

  // Generate or retrieve anonymous identifier (stored in localStorage)
  const getIdentifier = useCallback(() => {
    if (typeof window === 'undefined') return 'anonymous';
    let id = localStorage.getItem('temuclaude_id');
    if (!id) {
      id = `anon_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;
      localStorage.setItem('temuclaude_id', id);
    }
    return id;
  }, []);

  // Check usage on mount and after each query
  const checkUsage = useCallback(async () => {
    try {
      const identifier = getIdentifier();
      const res = await fetch('/api/usage/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier }),
      });
      const data = await res.json();
      if (data.allowed === false) {
        setLimitMessage(data.message);
        setShowUpgradeBanner(true);
      } else {
        setLimitMessage(null);
        setFreeQueriesUsed(data.queriesToday || 0);
      }
    } catch (err) {
      // Silently fail — don't block the user if the check endpoint is down
    }
  }, [getIdentifier]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    checkUsage();
  }, [checkUsage]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || status === 'submitted' || status === 'streaming') return;

    // Check if user has reached free tier limit
    if (limitMessage) {
      setShowUpgradeBanner(true);
      return;
    }

    const userMessage: Message = { role: 'user', content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setStatus('submitted');

    // Increment usage counter (fire and forget)
    const identifier = getIdentifier();
    fetch('/api/usage/check', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, inputTokens: 1000, outputTokens: 1000 }),
    }).then(() => checkUsage()).catch(() => {});

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [...messages, userMessage] }),
        signal: abortControllerRef.current?.signal,
      });

      if (!response.ok) throw new Error(`API returned ${response.status}`);

      setStatus('streaming');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';
      let orchestrationData: OrchestrationData | undefined;

      // Insert placeholder assistant bubble once
      streamingIdxRef.current = -1;
      setMessages((prev) => {
        const placeholderMsg: Message = { role: 'assistant', content: '' };
        streamingIdxRef.current = prev.length;
        return [...prev, placeholderMsg];
      });

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
                  const idx = streamingIdxRef.current;
                  setMessages((prev) => {
                    if (idx < 0 || idx >= prev.length) return prev;
                    const updated = [...prev];
                    updated[idx] = { role: 'assistant', content: assistantContent };
                    return updated;
                  });
                }
                if (data.orchestration) {
                  orchestrationData = data.orchestration;
                }
              } catch {}
            }
          }
        }
      }

      // Attach orchestration metadata to the streamed assistant message.
      if (orchestrationData) {
        const idx = streamingIdxRef.current;
        setMessages((prev) => {
          if (idx < 0 || idx >= prev.length) return prev;
          const updated = [...prev];
          updated[idx] = { ...updated[idx], orchestration: orchestrationData };
          return updated;
        });
      }

      streamingIdxRef.current = -1;
      setStatus('ready');
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setStatus('ready');
      } else {
        setStatus('error');
        setMessages((prev) => [...prev, { role: 'assistant', content: 'Something went wrong. Please try again.' }]);
      }
    }
  }, [input, status, messages, limitMessage, getIdentifier, checkUsage]);

  const handleStop = () => {
    abortControllerRef.current?.abort();
    setStatus('ready');
  };

  return (
    <>
      <Navbar />
      <div className="flex h-screen pt-16">
        <h1 className="sr-only">TemuClaude Playground</h1>

        <main className="flex-1 flex flex-col h-[calc(100vh-4rem)]" aria-label="TemuClaude Playground" id="main-content">
          {/* Free tier limit banner */}
          {showUpgradeBanner && limitMessage && (
            <div className="bg-accent-primary/10 border-b border-accent-primary/20 px-4 py-3">
              <div className="max-w-3xl mx-auto flex items-center justify-between gap-4">
                <p className="text-sm text-text-primary">{limitMessage}</p>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button onClick={() => setShowUpgradeBanner(false)} className="text-text-muted hover:text-text-primary text-xs" aria-label="Dismiss">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                  </button>
                  <a href="/pricing" className="btn-accent text-xs !py-1.5 !px-3">Upgrade</a>
                </div>
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 md:px-6 py-6">
            <div className="max-w-3xl mx-auto space-y-6">
              {/* Empty State */}
              {messages.length === 0 && (
                <div className="text-center pt-12">
                  <h2 className="text-2xl font-semibold text-text-primary mb-2">
                    Ask TemuClaude anything
                  </h2>
                  <p className="text-text-secondary mb-8">
                    One model. Eight minds behind the scenes. One superior answer.
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
                <div key={i} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
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

          {/* Input Bar */}
          <div className="border-t border-border-subtle bg-bg-primary p-4">
            <div className="max-w-3xl mx-auto">
              {/* Free tier counter & API toggle */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-text-muted">
                    {freeQueriesUsed < 20 ? `${20 - freeQueriesUsed} free queries left today` : 'Free queries used up for today'}
                  </span>
                  {freeQueriesUsed >= 12 && freeQueriesUsed < 20 && (
                    <a href="/pricing" className="text-xs text-accent-primary hover:underline">Upgrade for more →</a>
                  )}
                </div>
                <button
                  onClick={() => setShowQuickStart(prev => !prev)}
                  className="xl:hidden text-xs text-accent-primary hover:underline flex items-center gap-1 cursor-pointer"
                  aria-label="Toggle API Code Details"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
                  </svg>
                  API Code
                </button>
              </div>
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
                  placeholder="Ask TemuClaude anything..."
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
            </div>
          </div>
        </main>
        <QuickStartPane isOpen={showQuickStart} onClose={() => setShowQuickStart(false)} />
      </div>
    </>
  );
}

function QuickStartPane({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [activeTab, setActiveTab] = useState<'curl' | 'python' | 'node'>('curl');
  const [copied, setCopied] = useState(false);

  const snippets = {
    curl: `curl -X POST https://temuclaude.com/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"messages": [{"role": "user", "content": "hi"}]}'`,
    python: `import requests

url = "https://temuclaude.com/api/chat"
payload = {
    "messages": [
        {"role": "user", "content": "hi"}
    ]
}
res = requests.post(url, json=payload)
print(res.json()["choices"][0]["message"]["content"])`,
    node: `const fetch = require('node-fetch');

const url = "https://temuclaude.com/api/chat";
const payload = {
  messages: [
    { role: 'user', content: 'hi' }
  ]
};

fetch(url, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
})
.then(res => res.json())
.then(data => console.log(data.choices[0].message.content));`
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(snippets[activeTab]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const contentMarkup = (
    <>
      <h2 className="text-sm font-semibold text-text-primary mb-3">API Quick Start</h2>
      <p className="text-xs text-text-secondary mb-4">
        Integrate TemuClaude's unified 8-model orchestration pipeline in one API call.
      </p>

      {/* Tabs */}
      <div className="flex border-b border-border-subtle mb-4">
        {(['curl', 'python', 'node'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 text-center py-1 text-xs font-mono capitalize cursor-pointer border-b-2 transition-all ${
              activeTab === tab
                ? 'border-accent-primary text-accent-primary font-semibold'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            {tab === 'node' ? 'NodeJS' : tab}
          </button>
        ))}
      </div>

      {/* Code Area */}
      <div className="relative bg-bg-dark text-bg-tertiary rounded-md p-3 font-mono text-[10px] leading-normal overflow-x-auto min-h-[160px]">
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 p-1 bg-white/10 hover:bg-white/20 rounded text-[9px] text-text-inverse transition-colors"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
        <pre className="whitespace-pre">{snippets[activeTab]}</pre>
      </div>

      <div className="mt-6 border-t border-border-subtle pt-4 space-y-3">
        <h3 className="text-xs font-semibold text-text-primary">End-to-End Orchestration</h3>
        <ul className="space-y-2 text-[11px] text-text-secondary">
          <li className="flex gap-2">
            <span className="text-accent-olive">✓</span>
            <span>Mixture of Agents (MoA) synthesis</span>
          </li>
          <li className="flex gap-2">
            <span className="text-accent-olive">✓</span>
            <span>Monte Carlo Tree Search (MCTS)</span>
          </li>
          <li className="flex gap-2">
            <span className="text-accent-olive">✓</span>
            <span>Self-Play Logic Verification</span>
          </li>
        </ul>
      </div>
    </>
  );

  return (
    <>
      {/* Permanent desktop sidebar layout */}
      <aside className="hidden xl:flex flex-col w-80 border-l border-border-subtle bg-bg-secondary h-[calc(100vh-4rem)] p-4 overflow-y-auto shrink-0">
        {contentMarkup}
      </aside>

      {/* Slide-over mobile drawer layout */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 xl:hidden" onClick={onClose}>
          <div className="w-80 bg-bg-secondary h-full p-4 overflow-y-auto border-l border-border-subtle flex flex-col relative" onClick={(e) => e.stopPropagation()}>
            <button 
              onClick={onClose} 
              className="absolute top-4 right-4 text-text-muted hover:text-text-primary cursor-pointer"
              aria-label="Close API Code Pane"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
            <div className="pt-8">
              {contentMarkup}
            </div>
          </div>
        </div>
      )}
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

        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-accent-olive/20 flex items-center justify-center flex-shrink-0">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
            </div>
            <div>
              <div className="text-sm font-medium text-text-primary">Understanding your question</div>
              <div className="text-xs text-text-muted">Classified as: {data.taskType} · Routed to: {data.tier} tier</div>
            </div>
          </div>

          {data.models.length > 1 && (
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-accent-primary/20 flex items-center justify-center flex-shrink-0">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#E25822" strokeWidth="2"><circle cx="12" cy="12" r="3" /></svg>
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

          <div className="flex items-center gap-4 pt-2 border-t border-border-subtle text-xs text-text-muted">
            <span>Total: {data.totalLatency}s</span>
            <span>·</span>
            <span>{data.models.length} models</span>
          </div>
        </div>
      </div>
    </div>
  );
}