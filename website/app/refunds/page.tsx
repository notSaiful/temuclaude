import { Navbar } from '@/components/Navbar';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Refund Policy — Temuclaude',
  description: 'Refund and cancellation policy for Temuclaude subscriptions.',
};

export default function RefundsPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Refund Policy">
        <div className="container-max max-w-2xl mx-auto">
          <h1 className="text-3xl font-light text-text-primary mb-2" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Refund Policy</h1>
          <p className="text-sm text-text-muted mb-12">Last updated: July 4, 2026</p>

          <div className="space-y-8 text-sm text-text-secondary leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">1. 30-Day Money-Back Guarantee</h2>
              <p>We offer a 30-day money-back guarantee on all paid subscriptions. If you are not satisfied with Temuclaude within 30 days of your first payment, we will refund 100% of your subscription fee — no questions asked.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">2. How to Request a Refund</h2>
              <p>To request a refund:</p>
              <ol className="list-decimal list-inside mt-2 space-y-1">
                <li>Email ggs@temuclaude.com with the subject "Refund Request"</li>
                <li>Include your account email and the date of your subscription</li>
                <li>We process refunds within 5-7 business days</li>
                <li>Refunds are credited to your original payment method</li>
              </ol>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">3. Cancellation</h2>
              <p>You can cancel your subscription at any time:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Email ggs@temuclaude.com to cancel</li>
                <li>Cancellation takes effect at the end of your current billing cycle</li>
                <li>You retain access until the end of the paid period</li>
                <li>No further charges after cancellation</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">4. Pay-As-You-Go Refunds</h2>
              <p>Pay-as-you-go API charges are non-refundable once incurred, as they represent actual compute costs. However:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>If you are charged due to a bug or system error, we will refund the erroneous charges</li>
                <li>If your API key is compromised and used without your authorization (reported within 24 hours), we will refund the unauthorized charges</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">5. Enterprise Refunds</h2>
              <p>Enterprise subscriptions ($499/month) are eligible for the 30-day money-back guarantee on the first month only. Subsequent months are non-refundable but cancellable with 30 days notice.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">6. Non-Refundable Items</h2>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>API usage charges beyond the 30-day guarantee period</li>
                <li>Charges for queries that were successfully processed but yielded unsatisfactory AI responses</li>
                <li>Charges incurred after the 30-day guarantee window</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">7. Free Tier</h2>
              <p>The free tier (100 queries/day) is provided at no cost. No refunds are applicable as no payment was made.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">8. Dispute Resolution</h2>
              <p>If you have a dispute about a charge:</p>
              <ol className="list-decimal list-inside mt-2 space-y-1">
                <li>Contact us at ggs@temuclaude.com first — we resolve most issues within 48 hours</li>
                <li>If unresolved, you may file a dispute with Razorpay</li>
                <li>As a last resort, disputes will be resolved in the courts of Nagpur, Maharashtra, India</li>
              </ol>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">9. Changes to This Policy</h2>
              <p>We may update this Refund Policy at any time. Changes do not affect refunds for purchases made before the change date.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">10. Contact</h2>
              <p>For refund requests or questions: ggs@temuclaude.com</p>
            </section>
          </div>
        </div>
      </main>
    </>
  );
}