import { Navbar } from '@/components/Navbar';

const discussionAreas = [
  { title: 'Capacity', description: 'Agree on expected usage, rate limits, and credit allocation.' },
  { title: 'Deployment', description: 'Review hosting, data location, and access requirements.' },
  { title: 'Support', description: 'Define support contacts and response expectations in writing.' },
];

export default function EnterprisePage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Enterprise">
        <div className="container-max">
          <header className="text-center mb-14">
            <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-4" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Enterprise</h1>
            <p className="text-text-secondary mb-8 max-w-xl mx-auto">Enterprise access is scoped by request. Features, capacity, support, pricing, and service terms are agreed before activation.</p>
            <a href="mailto:hello@temuclaude.com" className="btn-accent">Contact sales</a>
          </header>

          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {discussionAreas.map((area) => <article key={area.title} className="card h-full"><h2 className="text-base font-semibold text-text-primary mb-2">{area.title}</h2><p className="text-sm text-text-secondary">{area.description}</p></article>)}
          </div>
        </div>
      </main>
    </>
  );
}
