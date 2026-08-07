import Link from 'next/link';

export default function HomePage() {
  return (
    <main id="main-content" className="min-h-screen bg-bg-primary px-6 py-24 text-text-primary">
      <div className="mx-auto max-w-3xl">
        <p className="font-mono text-sm text-accent-primary">TEMUCLAUDE API</p>
        <h1 className="mt-5 text-5xl font-semibold tracking-tight">Frontier-focused routing, without the sprawl.</h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-text-secondary">
          One OpenAI-compatible endpoint automatically routes general reasoning to GLM 5.2, implementation and autonomous workflows to Kimi K3, and code repair or review to Grok 4.5.
        </p>
        <pre className="mt-10 overflow-x-auto rounded-lg bg-bg-dark p-6 text-sm text-text-inverse"><code>{`curl https://temuclaude.com/v1/chat/completions \\
  -H "Authorization: Bearer $TEMUCLAUDE_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"temuclaude/temuclaude","messages":[{"role":"user","content":"Build a deployment workflow for my Next.js app"}]}'`}</code></pre>
        <Link href="/docs" className="mt-8 inline-block text-accent-primary underline underline-offset-4">Read the API documentation →</Link>
      </div>
    </main>
  );
}
