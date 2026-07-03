import { Navbar } from '@/components/Navbar';

const sections = [
  { title: 'Overview', items: ['Quickstart', 'Architecture', 'Models'] },
  { title: 'Features', items: ['Fusion', 'Self-Consistency', 'Code Verification', 'Self-QA Gate', 'Skills Auto-Loading', 'Adaptive Routing'] },
  { title: 'Benchmarks', items: ['Methodology', 'Reproducibility'] },
  { title: 'Self-Hosting', items: ['Docker', 'Fly.io'] },
];

export default function DocsPage() {
  return (
    <>
      <Navbar />
      <div className="pt-16 flex">
        <aside className="hidden md:block w-64 sticky top-16 h-[calc(100vh-4rem)] overflow-y-auto border-r border-border-subtle p-4" aria-label="Documentation navigation">
          {sections.map((s, i) => (
            <div key={i} className="mb-6">
              <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">{s.title}</h3>
              <ul className="space-y-1">
                {s.items.map((item, j) => (
                  <li key={j}><a href={'#' + item.toLowerCase().replace(/\s/g, '-')} className="text-sm text-text-secondary hover:text-accent-primary transition-colors block py-1">{item}</a></li>
                ))}
              </ul>
            </div>
          ))}
        </aside>
        <main className="flex-1 px-6 md:px-12 py-12" aria-label="Documentation">
          <div className="max-w-[680px] mx-auto">
            <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-text-muted mb-6">
              <a href="/" className="hover:text-accent-primary">Home</a><span>/</span><span className="text-text-primary">Docs</span>
            </nav>
            <h1 className="text-3xl font-semibold text-text-primary mb-2">Documentation</h1>
            <p className="text-text-secondary mb-8">Everything you need to use Timuclaude.</p>
            <section id="quickstart" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Quickstart</h2>
              <p className="text-text-secondary mb-4">Get started with Timuclaude in under 5 minutes.</p>
              <div className="bg-bg-dark text-bg-tertiary font-mono text-sm p-4 rounded-md mb-4 overflow-x-auto">
                <div className="flex items-center justify-between mb-2"><span className="text-xs text-text-muted">bash</span><button className="text-text-muted hover:text-text-inverse">Copy</button></div>
                <pre><code>pip install timuclaude{'\n'}timuclaude --start</code></pre>
              </div>
              <p className="text-sm text-text-secondary">Or use the <a href="/playground" className="text-accent-primary hover:underline">playground</a> — no installation required.</p>
            </section>
            <section id="architecture" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Architecture</h2>
              <p className="text-text-secondary mb-4">Timuclaude orchestrates 5 AI models using a 3-tier routing system:</p>
              <ul className="space-y-2 text-sm text-text-secondary">
                <li><strong className="text-text-primary">Trivial tier:</strong> Single cheap model (GPT-OSS 120B)</li>
                <li><strong className="text-text-primary">Medium tier:</strong> Specialist model based on task type</li>
                <li><strong className="text-text-primary">Hard tier:</strong> Fusion (3-5 models) + code verification + self-QA</li>
              </ul>
            </section>
            <section id="fusion" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Fusion</h2>
              <p className="text-text-secondary">For hard questions, Timuclaude sends the query to 3-5 models in parallel. A dynamic aggregator synthesizes the best parts of each response. The aggregator is selected dynamically based on task type.</p>
            </section>
            <section id="self-qa" className="mb-12">
              <h2 className="text-xl font-semibold text-text-primary mb-3">Self-QA Gate</h2>
              <p className="text-text-secondary">After generating a response, a verifier model scores the answer 0-10. If below 8, Timuclaude retries with feedback — up to 2 times.</p>
            </section>
            <p className="text-sm text-text-muted mt-12"><a href="https://github.com/notSaiful/timuclaude-research" className="text-accent-primary hover:underline" target="_blank" rel="noopener noreferrer">Edit this page on GitHub →</a></p>
          </div>
        </main>
      </div>
    </>
  );
}
