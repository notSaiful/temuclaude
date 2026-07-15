import { Navbar } from '@/components/Navbar';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service — TemuClaude',
  description: 'Terms for using the TemuClaude website, playground, and API.',
};

export default function TermsPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Terms of Service">
        <div className="container-max max-w-2xl mx-auto">
          <h1 className="text-3xl md:text-4xl font-serif text-text-primary mb-2" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Terms of Service</h1>
          <p className="text-sm text-text-muted mb-12">Last updated: July 15, 2026</p>
          <div className="space-y-8 text-sm text-text-secondary leading-relaxed">
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">1. Agreement</h2><p>By using TemuClaude, you agree to these terms. If you do not agree, do not use the service.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">2. Service</h2><p>TemuClaude provides a website, an authenticated playground, and an API that chooses from configured AI models and returns one answer. Current prices, credit limits, and availability are shown on the <a href="/pricing" className="text-accent-primary hover:underline">pricing page</a>.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">3. Accounts and keys</h2><p>You are responsible for activity under your account and API keys. Keep credentials private and notify us promptly if one is compromised.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">4. Acceptable use</h2><p>Do not use the service for illegal activity, abuse, harmful content, unauthorized access, resale without permission, or attempts to bypass security and usage limits.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">5. Billing</h2><p>Hosted checkout may be disabled while paid access is handled by request. Any recurring billing, overage, enterprise, or support terms must be presented and accepted before they apply.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">6. AI output</h2><p>AI output can be inaccurate, incomplete, or unsuitable. Verify important output before relying on it. TemuClaude is not a substitute for legal, medical, financial, or other professional advice.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">7. Your content</h2><p>You retain your rights in the prompts and material you provide. You permit TemuClaude and its configured providers to process that material only as needed to operate the service.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">8. Availability</h2><p>The service is provided as available. Models and providers may change or become unavailable, and requests may fail or take longer than expected.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">9. Liability</h2><p>To the extent allowed by law, TemuClaude is not liable for indirect losses or decisions made from AI output. Total liability is limited to the amount you paid for the service during the previous 12 months.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">10. Privacy and refunds</h2><p>See the <a href="/privacy" className="text-accent-primary hover:underline">privacy policy</a> and <a href="/refunds" className="text-accent-primary hover:underline">refund policy</a>.</p></section>
            <section><h2 className="text-lg font-semibold text-text-primary mb-3">11. Contact and law</h2><p>These terms are governed by the laws of India. Contact <a href="mailto:hello@temuclaude.com" className="text-accent-primary hover:underline">hello@temuclaude.com</a> with questions.</p></section>
          </div>
        </div>
      </main>
    </>
  );
}
