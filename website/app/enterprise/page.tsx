import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';

export default function EnterprisePage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Enterprise">
        <div className="container-max">
          <div className="text-center mb-16">
            <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-4" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Enterprise</h1>
            <p className="text-text-secondary mb-8 max-w-xl mx-auto">
              Scale TemuClaude across your team. Self-host on your infrastructure. Custom models, dedicated support, and SLA guarantees.
            </p>
            <a href="mailto:hello@temuclaude.com" className="btn-accent">Contact Sales</a>
          </div>

          <StaggerReveal className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            {[
              { title: 'SSO/SAML', desc: 'Single sign-on with your existing identity provider.' },
              { title: 'Self-Hosted', desc: 'Deploy on your own infrastructure with Docker or Fly.io. MIT licensed — full control.' },
              { title: 'SLA Guarantee', desc: '99.9% uptime with 4-hour response time for critical issues.' },
              { title: 'Custom Models', desc: 'Add your own fine-tuned models to the orchestration pool.' },
              { title: 'Team Management', desc: 'Role-based access control, audit logs, usage limits per seat.' },
              { title: 'Priority Routing', desc: 'Faster latency, dedicated model capacity, no rate limits.' },
            ].map((f, i) => (
              <StaggerItem key={i}>
                <div className="card h-full">
                  <h3 className="text-base font-semibold text-text-primary mb-1">{f.title}</h3>
                  <p className="text-sm text-text-secondary">{f.desc}</p>
                </div>
              </StaggerItem>
            ))}
          </StaggerReveal>

          <div className="text-center">
            <div className="card max-w-md mx-auto">
              <h3 className="text-lg font-semibold text-text-primary mb-2">$499/month</h3>
              <p className="text-sm text-text-secondary mb-4">Unlimited queries, 10 seats included, dedicated support. Contact us for custom enterprise pricing.</p>
              <a href="mailto:hello@temuclaude.com" className="btn-accent w-full">Contact Sales</a>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}