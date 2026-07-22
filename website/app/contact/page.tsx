import { Navbar } from '@/components/Navbar';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Contact Us — TemuClaude',
  description: 'Contact details for TemuClaude support, billing, legal, and enterprise enquiries.',
};

const contacts = [
  {
    label: 'General & Support Enquiries',
    value: 'hello@temuclaude.com',
    href: 'mailto:hello@temuclaude.com',
    note: 'Product help, account access, usage limits, custom models, and playground questions.',
  },
  {
    label: 'Phone Support (AI Voice Agent)',
    value: '+1 (725) 268-6198',
    href: 'tel:+17252686198',
    note: '24/7 AI-powered customer support, billing enquiries, and paid-plan activation help.',
  },
];

export default function ContactPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Contact Us">
        <div className="container-max max-w-3xl mx-auto">
          <h1 className="text-3xl md:text-4xl font-serif text-text-primary mb-2" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
            Contact Us
          </h1>
          <p className="text-sm text-text-muted mb-12">Last updated: July 9, 2026</p>

          <div className="grid md:grid-cols-2 gap-4 mb-10">
            {contacts.map((contact) => (
              <section key={contact.value} className="card h-full">
                <h2 className="text-base font-semibold text-text-primary mb-2">{contact.label}</h2>
                <a href={contact.href} className="text-sm font-medium text-accent-primary hover:underline">
                  {contact.value}
                </a>
                <p className="text-sm text-text-secondary mt-3">{contact.note}</p>
              </section>
            ))}
          </div>

          <div className="space-y-8 text-sm text-text-secondary leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">Business Information</h2>
              <ul className="list-disc list-inside space-y-1">
                <li><strong>Business name:</strong> TemuClaude</li>
                <li><strong>Service:</strong> AI orchestration SaaS, developer API access, and enterprise AI support</li>
                <li><strong>Operating location:</strong> Nagpur, Maharashtra, India</li>
                <li><strong>Phone:</strong> <a href="tel:+17252686198" className="text-accent-primary hover:underline">+1 (725) 268-6198</a></li>
                <li><strong>Email:</strong> <a href="mailto:hello@temuclaude.com" className="text-accent-primary hover:underline">hello@temuclaude.com</a></li>
                <li><strong>Website:</strong> <a href="https://temuclaude.com" className="text-accent-primary hover:underline">https://temuclaude.com</a></li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">Support Hours</h2>
              <p>Our phone line is attended 24/7 by our AI support agent. Support emails are monitored Monday to Friday, 10:00 AM to 6:00 PM India Standard Time, excluding public holidays.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3">Payment Support</h2>
              <p>For paid-plan access or billing questions, include your account email, preferred plan, expected monthly usage, and a short description of the issue. We usually respond within 2 business days.</p>
            </section>
          </div>
        </div>
      </main>
    </>
  );
}
