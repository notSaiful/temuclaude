const example = `curl https://temuclaude.com/v1/chat/completions \\
  -H "Authorization: Bearer $TEMUCLAUDE_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "temuclaude/temuclaude",
    "messages": [{"role":"user","content":"Review this failing TypeScript build"}],
    "stream": true
  }'`;

export default function DocsPage() {
  return (
    <main id="main-content" className="min-h-screen bg-bg-primary px-6 py-20 text-text-primary">
      <article className="mx-auto max-w-3xl">
        <p className="font-mono text-sm text-accent-primary">API DOCUMENTATION</p>
        <h1 className="mt-4 text-4xl font-semibold">One endpoint. Three purpose-built models.</h1>
        <p className="mt-5 text-lg leading-8 text-text-secondary">TemuClaude is an OpenAI-compatible API. Send a normal chat-completions request and the router selects exactly one primary model; the other approved models are used only if the primary is unavailable.</p>

        <h2 className="mt-12 text-2xl font-semibold">Endpoint</h2>
        <pre className="mt-4 overflow-x-auto rounded-lg bg-bg-dark p-5 text-sm text-text-inverse"><code>{example}</code></pre>

        <h2 className="mt-12 text-2xl font-semibold">Routing policy</h2>
        <ul className="mt-4 list-disc space-y-3 pl-6 text-text-secondary">
          <li><strong className="text-text-primary">GLM 5.2</strong> is the default for general reasoning, analysis, and planning.</li>
          <li><strong className="text-text-primary">Kimi K3</strong> handles implementation, coding, autonomous agents, deployment agents, and multi-agent workflows.</li>
          <li><strong className="text-text-primary">Grok 4.5</strong> handles debugging, code review, security review, incident analysis, and repair.</li>
        </ul>
        <p className="mt-5 text-text-secondary">Coding and agent-workflow requests receive a 12,000-token minimum completion budget, even when a client sends a smaller default, to prevent incomplete code artifacts after model reasoning.</p>
        <p className="mt-5 text-text-secondary">Responses include <code>X-TemuClaude-Route</code> and <code>X-TemuClaude-Model</code> headers for observability. The public API exposes one model ID: <code>temuclaude/temuclaude</code>.</p>

        <h2 className="mt-12 text-2xl font-semibold">Authentication</h2>
        <p className="mt-4 text-text-secondary">Pass your API key as a Bearer token or in the <code>x-api-key</code> header. API keys are server-side secrets; do not expose them in browser code.</p>
      </article>
    </main>
  );
}
