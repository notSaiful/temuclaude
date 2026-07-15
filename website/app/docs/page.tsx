import { Navbar } from '@/components/Navbar';

function CodeBlock({ code }: { code: string }) {
  return (
    <pre className="bg-bg-dark text-bg-tertiary font-mono text-sm p-4 rounded-md mb-4 overflow-x-auto whitespace-pre-wrap"><code>{code}</code></pre>
  );
}

const errorRows = [
  ['400', 'The request body is invalid.'],
  ['401', 'The API key or user session is missing or invalid.'],
  ['402', 'The account does not have enough credits.'],
  ['429', 'The account has reached its usage limit.'],
  ['503', 'No configured provider returned a usable answer.'],
];

export default function DocsPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Documentation">
        <div className="max-w-[760px] mx-auto">
          <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Documentation</h1>
          <p className="text-text-secondary mb-12">Use the playground or send an OpenAI-compatible request. The service chooses a suitable model and returns one answer.</p>

          <section className="mb-12" id="quickstart">
            <h2 className="text-xl font-semibold text-text-primary mb-3">Quick start</h2>
            <p className="text-text-secondary mb-4">Create an API key in the dashboard, store it securely, and send it as a bearer token.</p>
            <CodeBlock code={`curl https://temuclaude.com/v1/chat/completions \\
  -H "Authorization: Bearer $TEMUCLAUDE_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "temuclaude",
    "messages": [
      {"role": "user", "content": "What is the main point of this text?"}
    ]
  }'`} />
          </section>

          <section className="mb-12" id="request">
            <h2 className="text-xl font-semibold text-text-primary mb-3">Request fields</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead><tr className="border-b border-border-default text-left"><th className="py-2">Field</th><th className="py-2">Required</th><th className="py-2">Meaning</th></tr></thead>
                <tbody className="text-text-secondary">
                  <tr className="border-b border-border-subtle"><td className="py-2 font-mono">model</td><td>Yes</td><td>Use <code>temuclaude/temuclaude</code>, <code>temuclaude/temuclaude-pro</code>, or <code>temuclaude/temuclaude-lite</code>.</td></tr>
                  <tr className="border-b border-border-subtle"><td className="py-2 font-mono">messages</td><td>Yes</td><td>A non-empty array of system, user, and assistant messages.</td></tr>
                  <tr className="border-b border-border-subtle"><td className="py-2 font-mono">stream</td><td>No</td><td>Set to <code>true</code> for server-sent response chunks.</td></tr>
                  <tr className="border-b border-border-subtle"><td className="py-2 font-mono">temperature</td><td>No</td><td>A value from 0 to 2. Defaults to 0.6.</td></tr>
                  <tr><td className="py-2 font-mono">max_tokens</td><td>No</td><td>The requested output limit. Server-side limits still apply.</td></tr>
                </tbody>
              </table>
            </div>
          </section>

          <section className="mb-12" id="behavior">
            <h2 className="text-xl font-semibold text-text-primary mb-3">Routing behavior</h2>
            <ol className="list-decimal list-inside text-text-secondary space-y-2">
              <li>Authentication and usage limits are checked before a paid provider call.</li>
              <li>The request is classified by task and difficulty.</li>
              <li>Routine work starts with a lower-cost model.</li>
              <li>Difficult or high-risk work may use a specialist and an independent check.</li>
              <li>Usage is recorded after a response completes.</li>
            </ol>
            <p className="text-sm text-text-muted mt-4">Provider availability can change. A fallback may be used when the requested route is unavailable, but the response must still come from an approved model.</p>
          </section>

          <section className="mb-12" id="streaming">
            <h2 className="text-xl font-semibold text-text-primary mb-3">Streaming</h2>
            <p className="text-text-secondary mb-4">Set <code>stream</code> to <code>true</code>. The endpoint returns OpenAI-compatible server-sent events and ends with <code>[DONE]</code>.</p>
          </section>

          <section className="mb-12" id="errors">
            <h2 className="text-xl font-semibold text-text-primary mb-3">Errors</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead><tr className="border-b border-border-default text-left"><th className="py-2">Status</th><th className="py-2">Meaning</th></tr></thead>
                <tbody className="text-text-secondary">
                  {errorRows.map(([status, meaning]) => <tr key={status} className="border-b border-border-subtle"><td className="py-2 font-mono">{status}</td><td>{meaning}</td></tr>)}
                </tbody>
              </table>
            </div>
          </section>

          <section className="mb-12" id="privacy">
            <h2 className="text-xl font-semibold text-text-primary mb-3">Data and privacy</h2>
            <p className="text-text-secondary mb-3">Requests are sent to configured model providers to produce an answer. Provider privacy terms apply while they process the request.</p>
            <p className="text-text-secondary">TemuClaude records account usage and routing metadata needed to enforce limits and operate the service. See the <a className="text-accent-primary hover:underline" href="/privacy">privacy policy</a> for the current retention policy.</p>
          </section>

          <section id="help">
            <h2 className="text-xl font-semibold text-text-primary mb-3">Help</h2>
            <p className="text-text-secondary">Use the <a className="text-accent-primary hover:underline" href="/playground">playground</a> to test an account interactively or <a className="text-accent-primary hover:underline" href="/contact">contact support</a>.</p>
          </section>
        </div>
      </main>
    </>
  );
}
