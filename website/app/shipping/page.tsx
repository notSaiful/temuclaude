import { Navbar } from '@/components/Navbar';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Shipping and Digital Delivery Policy — TemuClaude',
  description: 'Digital delivery and shipping policy for TemuClaude subscriptions and API access.',
};

export default function ShippingPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Shipping and Digital Delivery Policy">
        <div className="container-max max-w-2xl mx-auto">
          <h1 className="text-3xl md:text-4xl font-serif text-text-primary mb-2" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
            Shipping and Digital Delivery Policy
          </h1>
          <p className="text-sm text-text-muted mb-12">Last updated: July 9, 2026</p>

          <div className="space-y-8 text-sm text-text-secondary leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">1. Digital-Only Service</h2>
              <p>TemuClaude provides digital software services, including web playground access, API access, usage dashboards, and enterprise AI orchestration support. We do not sell, ship, or deliver physical goods.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">2. Delivery Timeline</h2>
              <p>Free accounts are available immediately after sign-in. Paid-plan access is currently activated by request after account and billing confirmation. In most cases, access is available within 1 business day after confirmation.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">3. Delivery Method</h2>
              <p>Access is delivered through your TemuClaude account at <a href="/dashboard" className="text-accent-primary hover:underline">/dashboard</a>, the <a href="/playground" className="text-accent-primary hover:underline">playground</a>, and API credentials generated for eligible plans. Subscription and billing confirmations are sent to the account email.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">4. No Shipping Charges</h2>
              <p>Because TemuClaude is a digital service, there are no shipping charges, courier fees, import duties, or physical delivery timelines.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">5. Failed or Delayed Delivery</h2>
              <p>If paid access is confirmed but not activated within 1 business day, email <a href="mailto:hello@temuclaude.com" className="text-accent-primary hover:underline">hello@temuclaude.com</a> with your account email, selected plan, confirmation date, and payment reference if available. We will either activate access or issue an eligible refund under our <a href="/cancellation-refunds" className="text-accent-primary hover:underline">Cancellation and Refunds Policy</a>.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">6. Contact</h2>
              <p>For delivery or account activation questions, contact <a href="mailto:hello@temuclaude.com" className="text-accent-primary hover:underline">hello@temuclaude.com</a> or call <a href="tel:+17252686198" className="text-accent-primary hover:underline">+1 (725) 268-6198</a>.</p>
            </section>
          </div>
        </div>
      </main>
    </>
  );
}
