import { Navbar } from '@/components/Navbar';
import { PUBLIC_MODEL_ROLES } from '@/lib/model-catalog';

export default function ModelsPage() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6" aria-label="Model roles">
        <div className="container-max">
          <h1 className="text-3xl md:text-4xl font-light text-text-primary mb-3" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>Model roles</h1>
          <p className="text-text-secondary mb-4 max-w-2xl">TemuClaude does not call every model for every request. It starts with a suitable default and adds another model only when the task or a failed check justifies it.</p>
          <p className="text-sm text-text-muted mb-10 max-w-2xl">Availability depends on the configured provider. The runtime catalog is the source of truth and is checked before release.</p>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {PUBLIC_MODEL_ROLES.map((model) => (
              <article key={model.id} className="card h-full">
                <h2 className="text-lg font-semibold text-text-primary mb-1">{model.name}</h2>
                <div className="text-xs text-accent-primary mb-3">{model.role}</div>
                <p className="text-sm text-text-secondary">{model.description}</p>
              </article>
            ))}
          </div>
        </div>
      </main>
    </>
  );
}
