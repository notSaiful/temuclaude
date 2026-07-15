import { Navbar } from '@/components/Navbar';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy — TemuClaude',
  description: 'How TemuClaude handles account, usage, and request data.',
};

export default function PrivacyPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Privacy Policy">
        <div className="container-max max-w-2xl mx-auto">
          <h1 className="text-3xl md:text-4xl font-serif text-text-primary mb-2" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Privacy Policy</h1>
          <p className="text-sm text-text-muted mb-12">Last updated: July 15, 2026</p>
          <div className="space-y-8 text-sm text-text-secondary leading-relaxed">
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">1. Data we keep</h2><p>We keep account details, plan status, API-key hashes, credit balances, request counts, token counts, model activity, cost records, and service events needed to authenticate users, enforce limits, support billing, and operate the service.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">2. Request content</h2><p>Prompt and response content is sent to configured model providers to produce an answer. TemuClaude does not intentionally store playground or API message content in its usage records. The playground may store conversation history in your browser so you can resume it; clearing site data removes that local copy.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">3. Providers</h2><p>TemuClaude uses service providers such as Supabase for accounts and data, OpenRouter and selected model providers for AI responses, Google Cloud Run and Vercel for hosting, an email provider for messages, and a payment provider when billing is enabled. Each provider processes the minimum data needed for its role under its own terms.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">4. Security</h2><p>Connections use HTTPS. API keys are stored as hashes. Sensitive service credentials are kept in server-side environment variables or a secret manager. No security control can eliminate every risk.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">5. Cookies and local storage</h2><p>Authentication sessions, consent choices, and playground state may use browser cookies or local storage. TemuClaude does not need advertising cookies to provide the service.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">6. Retention</h2><p>We retain account, usage, billing, and security records only as long as needed to operate the service, meet legal obligations, resolve disputes, and prevent abuse. Provider retention policies may differ.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">7. Your choices</h2><p>You may request access, correction, export, or deletion of personal data, subject to legal and security requirements. You can also revoke API keys and clear locally stored playground conversations.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">8. Contact</h2><p>Send privacy questions or data requests to <a href="mailto:hello@temuclaude.com" className="text-accent-primary hover:underline">hello@temuclaude.com</a>.</p></section>
          </div>
        </div>
      </main>
    </>
  );
}
