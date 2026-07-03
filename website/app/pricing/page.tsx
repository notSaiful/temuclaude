import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';

const faqs = [
  { q: 'How is Timuclaude different from using GPT-5.5 directly?', a: 'GPT-5.5 is one model. Timuclaude orchestrates 5 models — fusing their answers, verifying with code, and quality-checking with self-QA. The result is measurably better, at 28x lower cost.' },
  { q: 'Is it really free?', a: 'Yes. Try it free in the playground. Self-host with our open-source code for unlimited free queries.' },
  { q: 'Which models does Timuclaude use?', a: 'GLM-5.2, DeepSeek V4 Pro, Kimi K2.6, MiniMax M3, Nemotron 3 Ultra, and GPT-OSS 120B. We route to the best model automatically — you never have to choose.' },
  { q: 'Can I self-host?', a: 'Yes. Clone the repo, install dependencies, and run. Full instructions in the docs. MIT licensed.' },
  { q: 'How does the orchestration work?', a: 'Timuclaude classifies your query, routes it to the best model(s), fuses multiple answers, verifies math with code execution, and quality-checks with a self-QA gate. You see the whole process in the playground.' },
  { q: 'Is my data stored?', a: 'No. Queries are processed in real-time and not stored.' },
  { q: 'What about enterprise?', a: 'Enterprise includes SSO, SLA, self-hosted deployment, dedicated support, and 200K queries/month.' },
  { q: 'Can I cancel anytime?', a: 'Yes. No contracts. Cancel anytime.' },
];

export default function PricingPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Pricing">
        <div className="container-max">
          <h1 className="text-3xl font-semibold text-text-primary mb-2 text-center">Pricing</h1>
          <p className="text-text-secondary text-center mb-12 max-w-xl mx-auto">Free to try in the playground. Pay only when you need more.</p>

          <StaggerReveal className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-20">
            {[
              { name: 'Self-Hosted', price: '$0', period: 'forever', desc: 'Run Timuclaude on your own infrastructure.', features: ['Unlimited queries', 'Full orchestration', 'All 5 models', 'Community support', 'MIT licensed'], cta: 'Start Free', featured: false },
              { name: 'Cloud', price: '$15', period: '/month', desc: 'Managed hosting. No setup required.', features: ['3K queries/month', 'Managed hosting', 'No setup required', 'Email support', 'All models included'], cta: 'Get Pro', featured: true },
              { name: 'Enterprise', price: '$499', period: '/month', desc: 'For teams and organizations.', features: ['200K queries/month', 'SLA guarantee', 'SSO/SAML', 'Self-hosted option', 'Dedicated support'], cta: 'Contact Sales', featured: false },
            ].map((tier, i) => (
              <StaggerItem key={i}>
                <div className={`card h-full ${tier.featured ? 'border-accent-primary border-2' : ''}`}>
                  {tier.featured && <div className="badge-accent mb-4 w-fit">Most Popular</div>}
                  <h3 className="text-lg font-semibold text-text-primary mb-1">{tier.name}</h3>
                  <div className="mb-1 flex items-baseline gap-1"><span className="text-3xl font-bold text-text-primary">{tier.price}</span><span className="text-sm text-text-muted">{tier.period}</span></div>
                  <p className="text-sm text-text-secondary mb-4">{tier.desc}</p>
                  <ul className="space-y-2 mb-6">{tier.features.map((f, j) => (
                    <li key={j} className="flex items-center gap-2 text-sm text-text-secondary"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>{f}</li>
                  ))}</ul>
                  <a href={tier.cta === 'Contact Sales' ? '/enterprise' : '/playground'} className={tier.featured ? 'btn-accent w-full' : 'btn-secondary w-full'}>{tier.cta}</a>
                </div>
              </StaggerItem>
            ))}
          </StaggerReveal>

          <section className="max-w-2xl mx-auto">
            <h2 className="text-xl font-semibold text-text-primary mb-6 text-center">Frequently Asked Questions</h2>
            <div className="space-y-4">{faqs.map((faq, i) => (
              <div key={i} className="card"><h3 className="text-sm font-semibold text-text-primary mb-2">{faq.q}</h3><p className="text-sm text-text-secondary">{faq.a}</p></div>
            ))}</div>
          </section>
        </div>
      </main>
    </>
  );
}