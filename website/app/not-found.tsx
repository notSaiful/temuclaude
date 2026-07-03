import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-bg-primary">
      <div className="text-center">
        <div className="text-8xl font-bold text-accent-primary mb-4">404</div>
        <h1 className="text-2xl font-semibold text-text-primary mb-2">Page not found</h1>
        <p className="text-text-secondary mb-8 max-w-md">The page you're looking for doesn't exist or has been moved.</p>
        <div className="flex gap-3 justify-center">
          <Link href="/" className="btn-primary">Back to Home</Link>
          <Link href="/playground" className="btn-secondary">Try the Playground</Link>
        </div>
      </div>
    </div>
  );
}
