import Link from 'next/link';

/** Minimal navigation for the API documentation site. */
export function Navbar() {
  return (
    <nav className="border-b border-border-subtle bg-bg-primary px-6 py-4">
      <div className="mx-auto flex max-w-5xl items-center justify-between">
        <Link href="/" className="font-semibold text-text-primary">TemuClaude</Link>
        <Link href="/docs" className="text-sm text-text-secondary hover:text-text-primary">API Docs</Link>
      </div>
    </nav>
  );
}
