import { Navbar } from '@/components/Navbar';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service — TemuClaude',
  description: 'Terms of Service for TemuClaude AI orchestration platform.',
};

export default function TermsPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Terms of Service">
        <div className="container-max max-w-2xl mx-auto">
          <h1 className="text-3xl font-light text-text-primary mb-2" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Terms of Service</h1>
          <p className="text-sm text-text-muted mb-12">Last updated: July 4, 2026</p>

          <div className="space-y-8 text-sm text-text-secondary leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">1. Acceptance of Terms</h2>
              <p>By using TemuClaude ("the Service"), you agree to these Terms of Service. If you do not agree, do not use the Service. The Service is provided by TemuClaude ("we", "us", "our").</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">2. Description of Service</h2>
              <p>TemuClaude is an AI orchestration platform that routes queries to multiple AI models, fuses their responses, and returns a single answer. The Service includes:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Playground (free tier subject to current usage limits)</li>
                <li>Developer subscription ($15/month, 50,000 queries/month)</li>
                <li>Pro subscription ($49/month, 500,000 queries/month)</li>
                <li>Pay-as-you-go API ($0.50/M input, $2.00/M output tokens)</li>
                <li>Enterprise subscription ($499/month, unlimited queries)</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">3. Acceptable Use</h2>
              <p>You agree NOT to:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Use the Service for illegal activities</li>
                <li>Generate content that is harmful, hateful, or discriminatory</li>
                <li>Attempt to reverse engineer, decompile, or extract our orchestration logic</li>
                <li>Resell or redistribute the Service without written permission</li>
                <li>Exceed the query limits of your plan</li>
                <li>Use automated bots to circumvent rate limits</li>
                <li>Use the Service to train competing AI models</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">4. Subscription Terms</h2>
              <p>Subscriptions are billed monthly via Razorpay. By subscribing, you agree to:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Pay the monthly fee in advance</li>
                <li>Allow automatic renewal until cancelled</li>
                <li>Cancel with 30 days written notice</li>
                <li>Not exceed the query limit of your plan</li>
              </ul>
              <p className="mt-2">If you exceed your plan's query limit, additional queries will be billed at pay-as-you-go rates ($0.50/M input, $2.00/M output).</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">5. API Usage</h2>
              <p>API access is available on Developer, Pro, and Enterprise plans. You are responsible for:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Keeping your API key secure</li>
                <li>All usage under your API key</li>
                <li>Notifying us within 24 hours of key compromise</li>
              </ul>
              <p className="mt-2">API rate limits: 100 requests/minute (Pro), 1,000 requests/minute (Enterprise).</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">6. Intellectual Property</h2>
              <p>We retain all intellectual property rights to the Service, including the orchestration logic, routing algorithms, and model pool configuration. You retain all rights to your queries and the responses you receive.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">7. Data and Privacy</h2>
              <p>We do not store your queries or responses. All processing is real-time. See our <a href="/privacy" className="text-accent-primary hover:underline">Privacy Policy</a> for details.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">8. Limitation of Liability</h2>
              <p>The Service is provided "as is" without warranties of any kind. We are not liable for:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Inaccurate or incorrect AI responses</li>
                <li>Service interruptions or downtime</li>
                <li>Loss of data or profits</li>
                <li>Third-party model failures (OpenRouter, model providers)</li>
              </ul>
              <p className="mt-2">Our total liability shall not exceed the amount paid in the preceding 12 months.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">9. AI-Generated Content</h2>
              <p>AI responses may be inaccurate, biased, or incomplete. You are responsible for verifying AI-generated content before relying on it. The Service is not a substitute for professional advice (legal, medical, financial).</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">10. Refunds</h2>
              <p>See our <a href="/refunds" className="text-accent-primary hover:underline">Refund Policy</a> for details on refunds and cancellations.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">11. Changes to Terms</h2>
              <p>We may update these Terms at any time. Continued use of the Service constitutes acceptance of updated Terms. We will notify subscribers of material changes via email.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">12. Governing Law</h2>
              <p>These Terms are governed by the laws of India. Disputes will be resolved in the courts of Nagpur, Maharashtra, India.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">13. Contact</h2>
              <p>For questions about these Terms, contact us at: ggs@temuclaude.com</p>
            </section>
          </div>
        </div>
      </main>
    </>
  );
}
