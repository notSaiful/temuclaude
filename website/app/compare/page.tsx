'use client';

import { useState, useCallback } from 'react';
import { Navbar } from '@/components/Navbar';

const presetQuestions = [
  'Prove that the sum of two odd numbers is always even.',
  'Explain the difference between supervised and unsupervised learning.',
  'Write a Python function to check if a number is prime.',
  'If all roses are flowers, and some flowers fade quickly, can we conclude that some roses fade quickly?',
  'What causes the seasons on Earth?',
  'Write a haiku about artificial intelligence.',
];

interface CompareResult {
  content: string;
  tokens: number;
  time: number;
  error?: string;
}

interface ApiResponse {
  temuclaude: CompareResult;
  single: CompareResult;
  model_name: string;
}

export default function ComparePage() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [error, setError] = useState('');
  const [vote, setVote] = useState<'temuclaude' | 'single' | null>(null);
  const [revealed, setRevealed] = useState(false);

  const handleCompare = useCallback(async () => {
    if (!question.trim()) {
      setError('Type a question first.');
      return;
    }
    setError('');
    setResult(null);
    setVote(null);
    setRevealed(false);
    setLoading(true);

    try {
      const r = await fetch('/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [{ role: 'user', content: question }],
          temperature: 0.6,
          max_tokens: 2048,
        }),
      });
      if (!r.ok) throw new Error('API error');
      const data: ApiResponse = await r.json();
      setResult(data);
    } catch (e) {
      setError('Failed to get comparison. Try again.');
    } finally {
      setLoading(false);
    }
  }, [question]);

  const handlePreset = (q: string) => {
    setQuestion(q);
    setResult(null);
    setVote(null);
    setRevealed(false);
  };

  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6 min-h-screen" aria-label="Live Comparison">
        <div className="container-max">
          {/* Header */}
          <div className="mb-8 max-w-2xl">
            <h1 className="text-3xl md:text-4xl font-serif text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
              TemuClaude vs single model. Live.
            </h1>
            <p className="text-text-secondary">
              Type any question. We&apos;ll send it to both TemuClaude (full 8-model orchestration)
              and a single model (GLM-5.2 alone). You see both answers side by side.
              Judge for yourself.
            </p>
          </div>

          {/* Question input */}
          <div className="mb-6">
            <div className="flex gap-3 mb-3">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !loading && handleCompare()}
                placeholder="Ask anything..."
                className="flex-1 px-4 py-3 rounded-md border border-border-default bg-white text-text-primary text-sm focus:border-accent-primary focus:outline-none transition-colors"
                disabled={loading}
              />
              <button
                onClick={handleCompare}
                disabled={loading || !question.trim()}
                className="btn-accent whitespace-nowrap"
              >
                {loading ? (
                  <>
                    <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Comparing...
                  </>
                ) : (
                  <>
                    Compare
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
                  </>
                )}
              </button>
            </div>

            {/* Preset questions */}
            <div className="flex flex-wrap gap-2">
              {presetQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handlePreset(q)}
                  disabled={loading}
                  className="text-xs px-3 py-1.5 rounded-full border border-border-default text-text-muted hover:border-accent-primary hover:text-accent-primary transition-colors disabled:opacity-50"
                >
                  {q.length > 50 ? q.slice(0, 50) + '...' : q}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-md border border-accent-fig/30 bg-accent-fig/5 text-sm text-accent-fig">
              {error}
            </div>
          )}

          {/* Results */}
          {loading && (
            <div className="grid md:grid-cols-2 gap-6">
              <div className="card" style={{ padding: '24px' }}>
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-accent-primary animate-pulse" />
                  <span className="text-sm font-semibold text-text-primary">Response A</span>
                </div>
                <div className="space-y-2">
                  <div className="h-4 bg-bg-tertiary/40 rounded animate-pulse" style={{ width: '90%' }} />
                  <div className="h-4 bg-bg-tertiary/40 rounded animate-pulse" style={{ width: '75%' }} />
                  <div className="h-4 bg-bg-tertiary/40 rounded animate-pulse" style={{ width: '85%' }} />
                  <div className="h-4 bg-bg-tertiary/40 rounded animate-pulse" style={{ width: '60%' }} />
                </div>
              </div>
              <div className="card" style={{ padding: '24px' }}>
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-accent-olive animate-pulse" />
                  <span className="text-sm font-semibold text-text-primary">Response B</span>
                </div>
                <div className="space-y-2">
                  <div className="h-4 bg-bg-tertiary/40 rounded animate-pulse" style={{ width: '80%' }} />
                  <div className="h-4 bg-bg-tertiary/40 rounded animate-pulse" style={{ width: '70%' }} />
                  <div className="h-4 bg-bg-tertiary/40 rounded animate-pulse" style={{ width: '90%' }} />
                  <div className="h-4 bg-bg-tertiary/40 rounded animate-pulse" style={{ width: '55%' }} />
                </div>
              </div>
            </div>
          )}

          {result && !loading && (
            <>
              {/* Side by side comparison */}
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                {/* TemuClaude (Response A) */}
                <div className="card flex flex-col" style={{ padding: '24px', borderColor: revealed ? 'rgba(226,88,34,0.3)' : undefined }}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ background: '#E25822' }} />
                      <span className="text-sm font-semibold text-text-primary">
                        {revealed ? 'TemuClaude (8-model orchestration)' : 'Response A'}
                      </span>
                    </div>
                    <div className="flex gap-3 text-xs text-text-muted font-mono">
                      <span>{(result.temuclaude.time / 1000).toFixed(1)}s</span>
                      <span>·</span>
                      <span>{result.temuclaude.tokens.toLocaleString()} tokens</span>
                    </div>
                  </div>
                  <div
                    className="text-sm text-text-primary leading-relaxed flex-1 overflow-y-auto"
                    style={{ maxHeight: '500px', whiteSpace: 'pre-wrap' }}
                  >
                    {result.temuclaude.content || result.temuclaude.error || 'No response'}
                  </div>
                  {revealed && (
                    <div className="mt-4 pt-4 border-t border-border-subtle">
                      <span className="badge-accent text-xs">8 models · MoA fusion · QA gate · reflexion</span>
                    </div>
                  )}
                </div>

                {/* Single model (Response B) */}
                <div className="card flex flex-col" style={{ padding: '24px', borderColor: revealed ? 'rgba(120,140,93,0.3)' : undefined }}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ background: '#788C5D' }} />
                      <span className="text-sm font-semibold text-text-primary">
                        {revealed ? `${result.model_name} (single model)` : 'Response B'}
                      </span>
                    </div>
                    <div className="flex gap-3 text-xs text-text-muted font-mono">
                      <span>{(result.single.time / 1000).toFixed(1)}s</span>
                      <span>·</span>
                      <span>{result.single.tokens.toLocaleString()} tokens</span>
                    </div>
                  </div>
                  <div
                    className="text-sm text-text-primary leading-relaxed flex-1 overflow-y-auto"
                    style={{ maxHeight: '500px', whiteSpace: 'pre-wrap' }}
                  >
                    {result.single.content || result.single.error || 'No response'}
                  </div>
                  {revealed && (
                    <div className="mt-4 pt-4 border-t border-border-subtle">
                      <span className="badge-muted text-xs">1 model · no orchestration · no QA</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Vote + reveal */}
              {!revealed && (
                <div className="text-center mb-6">
                  <p className="text-sm text-text-muted mb-4">Which response is better?</p>
                  <div className="flex items-center justify-center gap-3">
                    <button
                      onClick={() => { setVote('temuclaude'); setRevealed(true); }}
                      className="btn-secondary"
                    >
                      Response A is better
                    </button>
                    <button
                      onClick={() => { setVote('single'); setRevealed(true); }}
                      className="btn-secondary"
                    >
                      Response B is better
                    </button>
                    <button
                      onClick={() => setRevealed(true)}
                      className="text-sm text-text-muted hover:text-accent-primary transition-colors"
                    >
                      Just reveal
                    </button>
                  </div>
                </div>
              )}

              {revealed && (
                <div className="text-center mb-6">
                  {vote === 'temuclaude' && (
                    <p className="text-sm text-accent-primary font-semibold">
                      ✓ You picked TemuClaude (8-model orchestration). That&apos;s Response A.
                    </p>
                  )}
                  {vote === 'single' && (
                    <p className="text-sm text-accent-olive font-semibold">
                      You picked the single model (Response B). Fair enough — for simple questions, one model can be enough.
                    </p>
                  )}
                  {!vote && (
                    <p className="text-sm text-text-muted">
                      Response A = TemuClaude (8 models, full pipeline). Response B = {result.model_name} (single model, no orchestration).
                    </p>
                  )}
                  <button
                    onClick={() => { setResult(null); setVote(null); setRevealed(false); }}
                    className="mt-4 text-sm text-accent-primary hover:underline"
                  >
                    Try another question →
                  </button>
                </div>
              )}
            </>
          )}

          {/* How it works */}
          {!result && !loading && (
            <div className="max-w-2xl mt-12">
              <h2 className="text-xl font-semibold text-text-primary mb-4">How this works</h2>
              <div className="space-y-3 text-sm text-text-secondary">
                <p>
                  <strong className="text-text-primary">TemuClaude (Response A)</strong> runs the full pipeline:
                  classifies your question, routes to the best models, runs 3 models in parallel for hard questions,
                  fuses their answers, scores quality with an independent QA judge, and retries if the score is low.
                </p>
                <p>
                  <strong className="text-text-primary">Single model (Response B)</strong> is just GLM-5.2 alone —
                  one model, one call, no orchestration. This is what most AI APIs give you.
                </p>
                <p>
                  For simple questions, both might be similar. For hard questions — math, reasoning, complex explanations —
                  the difference should be visible. Try it.
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </>
  );
}