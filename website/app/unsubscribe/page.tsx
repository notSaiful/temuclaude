import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Unsubscribe — TemuClaude',
  description: 'Unsubscribe from TemuClaude email communications.',
  robots: 'noindex, follow',
};

export default function UnsubscribePage() {
  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <a href="/" className="text-2xl font-light text-text-primary" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
            TemuClaude
          </a>
        </div>
        <div className="bg-bg-secondary rounded-xl border border-border-subtle p-8">
          <h1 className="text-2xl font-light text-text-primary mb-4" style={{ fontWeight: 300 }}>
            Unsubscribe
          </h1>
          <p className="text-text-secondary mb-6 text-sm leading-relaxed">
            We respect your privacy. To unsubscribe from TemuClaude email communications,
            send an email to:
          </p>
          <div className="bg-bg-tertiary rounded-lg p-4 mb-6">
            <p className="text-primary font-mono text-sm">marketing@temuclaude.com</p>
            <p className="text-text-tertiary text-xs mt-1">Subject: Unsubscribe</p>
          </div>
          <p className="text-text-secondary text-sm mb-6">
            We will remove your email from our list within 48 hours.
            You may still receive transactional emails (billing, security, API notices) as required.
          </p>
          <a href="/" className="block text-center text-primary text-sm hover:underline">
            Return to TemuClaude
          </a>
        </div>
        <p className="text-center text-text-tertiary text-xs mt-6">
          TemuClaude · MIT Licensed · 25% of profit to charity
        </p>
      </div>
    </div>
  );
}