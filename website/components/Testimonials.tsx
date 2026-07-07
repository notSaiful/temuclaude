'use client';

import { motion } from 'framer-motion';

const testimonials = [
  {
    quote: "TemuClaude gives me better answers than GPT-5 for coding questions, at a fraction of the cost. The orchestration metadata is gold — I can see exactly which models contributed.",
    name: "Alex Chen",
    role: "Backend Engineer",
    initials: "AC",
  },
  {
    quote: "I replaced my $200/mo API bill with TemuClaude's free tier. The fusion pipeline handles my math homework better than any single model I've tried.",
    name: "Priya Sharma",
    role: "CS Student",
    initials: "PS",
  },
  {
    quote: "Open source, MIT licensed, transparent pipeline. This is how AI APIs should be built. No black boxes, no markup, just code.",
    name: "Marcus Webb",
    role: "Indie Hacker",
    initials: "MW",
  },
];

export function Testimonials() {
  return (
    <section className="py-20 px-6 bg-bg-secondary">
      <div className="container-max">
        <div className="mb-12 max-w-2xl mx-auto text-center">
          <h2
            className="text-3xl md:text-4xl font-serif text-text-primary mb-3"
            style={{ fontWeight: 300, letterSpacing: '-0.02em' }}
          >
            Trusted by builders
          </h2>
          <p className="text-text-secondary">
            Early users are already shipping with TemuClaude.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {testimonials.map((t, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.5, delay: i * 0.1, ease: [0.25, 1, 0.5, 1] }}
              className="bg-white rounded-md p-6 border border-border-subtle"
              style={{
                boxShadow: '0px 0px 0px 1px rgba(26, 24, 22, 0.04)',
              }}
            >
              {/* Quote mark */}
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="#E25822"
                opacity="0.2"
                className="mb-3"
              >
                <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.51.88-4.012 2.959-4.012 5.849h3.017v10h-8.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.511.88-4.013 2.959-4.013 5.849h3.017v10h-9z" />
              </svg>

              <p className="text-sm text-text-secondary leading-relaxed mb-6">
                {t.quote}
              </p>

              <div className="flex items-center gap-3">
                {/* Avatar with initials */}
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium shrink-0"
                  style={{ backgroundColor: 'rgba(226, 88, 34, 0.12)', color: '#E25822' }}
                >
                  {t.initials}
                </div>
                <div>
                  <div className="text-sm font-medium text-text-primary">{t.name}</div>
                  <div className="text-xs text-text-muted">{t.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}