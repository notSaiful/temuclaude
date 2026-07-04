import { Navbar } from '@/components/Navbar';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy — Temuclaude',
  description: 'Privacy Policy for Temuclaude AI orchestration platform.',
};

export default function PrivacyPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Privacy Policy">
        <div className="container-max max-w-2xl mx-auto">
          <h1 className="text-3xl font-light text-text-primary mb-2" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Privacy Policy</h1>
          <p className="text-sm text-text-muted mb-12">Last updated: July 4, 2026</p>

          <div className="space-y-8 text-sm text-text-secondary leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">1. Our Principle</h2>
              <p>We do not store your queries. We do not store your responses. We do not sell your data. All processing is real-time and ephemeral.</p>
              <p className="mt-2">This is not just a policy — it is built into our architecture. Queries are processed in memory and discarded. No persistent storage of conversation content.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">2. What We Collect</h2>
              <p>To provide the Service, we collect:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong>Email address</strong> — when you subscribe to a paid plan (for billing and account management)</li>
                <li><strong>Payment information</strong> — processed by Razorpay (we never see or store your card details)</li>
                <li><strong>Usage counts</strong> — number of queries per day/month (to enforce plan limits). We store the count, NOT the query content.</li>
                <li><strong>API keys</strong> — hashed and stored securely for authentication</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">3. What We Do NOT Collect</h2>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Query content — we do not store what you ask</li>
                <li>Response content — we do not store what the AI answers</li>
                <li>Conversation history — no chat logs are persisted</li>
                <li>IP addresses — not logged for analytics</li>
                <li>Browsing data — no tracking pixels, no cookies (except essential)</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">4. How We Use Your Data</h2>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Email: to send billing receipts, subscription notifications, and important service updates</li>
                <li>Usage counts: to enforce plan limits and prevent abuse</li>
                <li>Payment data: processed by Razorpay for subscription billing</li>
              </ul>
              <p className="mt-2">We do NOT use your data to train AI models. We do NOT use your data for advertising. We do NOT share your data with third parties.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">5. Data Processors</h2>
              <p>We use the following third-party services to operate the Service:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong>Razorpay</strong> — payment processing (PCI-DSS compliant, we never see card details)</li>
                <li><strong>OpenRouter</strong> — AI model hosting (queries are forwarded to their models; their privacy policy applies to query data in transit)</li>
                <li><strong>Vercel</strong> — website hosting and API infrastructure</li>
              </ul>
              <p className="mt-2">Each processor has their own privacy policy. We have data processing agreements in place and only share the minimum data necessary to provide the Service.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">6. Data Security</h2>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>API keys are hashed with SHA-256 before storage</li>
                <li>Payment processing is handled by Razorpay (PCI-DSS Level 1 compliant)</li>
                <li>All API communication uses HTTPS/TLS encryption</li>
                <li>Database access is restricted and audited</li>
                <li>No plaintext payment data is ever stored on our servers</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">7. Your Rights (GDPR / CCPA)</h2>
              <p>You have the right to:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Access your data — request a copy of all data we hold about you</li>
                <li>Correct your data — request correction of inaccurate information</li>
                <li>Delete your data — request deletion of your account and associated data</li>
                <li>Export your data — receive your data in JSON format</li>
                <li>Object to processing — request that we stop processing your data</li>
              </ul>
              <p className="mt-2">To exercise these rights, email us at ggs@temuclaude.com. We respond within 30 days.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">8. Data Retention</h2>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Account data (email, plan): retained while your account is active, deleted within 30 days of account closure</li>
                <li>Usage counts: retained for 90 days, then automatically purged</li>
                <li>Payment records: retained for 7 years (tax compliance, as required by Indian law)</li>
                <li>API keys: deleted immediately upon revocation</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">9. Cookies</h2>
              <p>We use only essential cookies:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Anonymous identifier (localStorage) — to track free tier usage across sessions</li>
                <li>Cookie consent — to remember your consent choice</li>
              </ul>
              <p className="mt-2">We do NOT use analytics cookies, advertising cookies, or social media tracking cookies.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">10. Children's Privacy</h2>
              <p>The Service is not intended for children under 13. We do not knowingly collect data from children. If you believe a child has provided us data, contact us and we will delete it immediately.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">11. Data Breach Notification</h2>
              <p>In the event of a data breach, we will notify affected users within 72 hours of discovery, as required by GDPR Article 34.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">12. Changes to This Policy</h2>
              <p>We may update this Privacy Policy at any time. We will notify subscribers of material changes via email. Continued use of the Service constitutes acceptance of the updated policy.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">13. Contact</h2>
              <p>For privacy questions or data requests, contact: ggs@temuclaude.com</p>
            </section>
          </div>
        </div>
      </main>
    </>
  );
}