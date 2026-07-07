'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { label: 'Models', href: '/models' },
  { label: 'Playground', href: '/playground' },
  { label: 'Docs', href: '/docs', hasDropdown: true },
  { label: 'Benchmarks', href: '/benchmarks' },
  { label: 'Pricing', href: '/pricing' },
];

const docsSubmenu = [
  { label: 'Quickstart', href: '/docs' },
  { label: 'API Reference', href: '/docs#api' },
  { label: 'Models', href: '/docs#models' },
  { label: 'Configuration', href: '/docs#config' },
  { label: 'Self-Hosting', href: '/docs#self-hosting' },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [docsOpen, setDocsOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  return (
    <>
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-250 ease-spring ${
          scrolled
            ? 'bg-bg-primary/85 backdrop-blur-md border-b border-border-subtle'
            : 'bg-transparent'
        }`}
        style={{ height: '64px' }}
        aria-label="Main navigation"
      >
        <div className="container-max h-full flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2" aria-label="TemuClaude home">
            {/* The Spark — small core, frontier output */}
            <svg width="28" height="28" viewBox="0 0 100 100" className="shrink-0" aria-hidden="true">
              <circle cx="50" cy="50" r="11" fill="#E25822"/>
              <line x1="50" y1="50" x2="50" y2="10" stroke="#E25822" strokeWidth="4.5" stroke-linecap="round"/>
              <line x1="50" y1="50" x2="79" y2="21" stroke="#E25822" strokeWidth="4.5" stroke-linecap="round"/>
              <line x1="50" y1="50" x2="90" y2="50" stroke="#E25822" strokeWidth="4.5" stroke-linecap="round"/>
              <line x1="50" y1="50" x2="79" y2="79" stroke="#E25822" strokeWidth="4.5" stroke-linecap="round"/>
              <line x1="50" y1="50" x2="50" y2="90" stroke="#E25822" strokeWidth="4.5" stroke-linecap="round"/>
              <line x1="50" y1="50" x2="21" y2="79" stroke="#E25822" strokeWidth="4.5" stroke-linecap="round"/>
              <line x1="50" y1="50" x2="10" y2="50" stroke="#E25822" strokeWidth="4.5" stroke-linecap="round"/>
              <line x1="50" y1="50" x2="21" y2="21" stroke="#E25822" strokeWidth="4.5" stroke-linecap="round"/>
            </svg>
            <span className="text-lg font-semibold tracking-tight text-text-primary">
              TemuClaude
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-8">
            {navItems.map((item) =>
              item.hasDropdown ? (
                <div
                  key={item.href}
                  className="relative"
                  onMouseEnter={() => setDocsOpen(true)}
                  onMouseLeave={() => setDocsOpen(false)}
                >
                  <Link
                    href={item.href}
                    className={`nav-link inline-flex items-center gap-1 ${
                      pathname === item.href || pathname?.startsWith(item.href + '/')
                        ? 'nav-link-active'
                        : ''
                    }`}
                    aria-current={pathname === item.href ? 'page' : undefined}
                  >
                    {item.label}
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className={`transition-transform ${docsOpen ? 'rotate-180' : ''}`}>
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </Link>
                  {docsOpen && (
                    <div
                      className="absolute top-full left-0 mt-1 w-48 bg-white border border-border-subtle rounded-sm py-2"
                      style={{ boxShadow: '0px 0px 0px 1px rgba(26, 24, 22, 0.08), rgba(26, 24, 22, 0.05) 0px 4px 24px' }}
                    >
                      {docsSubmenu.map((sub) => (
                        <Link
                          key={sub.href}
                          href={sub.href}
                          className="block px-4 py-2 text-sm text-text-secondary hover:bg-bg-secondary hover:text-text-primary transition-colors"
                        >
                          {sub.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`nav-link ${
                    pathname === item.href || pathname?.startsWith(item.href + '/')
                      ? 'nav-link-active'
                      : ''
                  }`}
                  aria-current={pathname === item.href ? 'page' : undefined}
                >
                  {item.label}
                </Link>
              )
            )}
          </div>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-3">
            <Link href="/playground" className="btn-primary">
              Try the Playground
            </Link>
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
            aria-expanded={mobileOpen}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1A1816" strokeWidth="2" strokeLinecap="round">
              {mobileOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </>
              ) : (
                <>
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </>
              )}
            </svg>
          </button>
        </div>
      </nav>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 md:hidden"
          onClick={() => setMobileOpen(false)}
        >
          <div className="absolute inset-0 bg-black/30" />
          <nav
            className="absolute top-0 right-0 bottom-0 w-72 bg-bg-primary border-l border-border-subtle flex flex-col"
            onClick={(e) => e.stopPropagation()}
            aria-label="Mobile navigation"
          >
            <div className="p-6 flex flex-col gap-1 mt-16">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`py-3 px-4 rounded-sm text-base font-medium transition-colors ${
                    pathname === item.href
                      ? 'bg-bg-secondary text-text-primary'
                      : 'text-text-secondary hover:bg-bg-secondary hover:text-text-primary'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
              <Link
                href="/playground"
                onClick={() => setMobileOpen(false)}
                className="btn-primary mt-4 w-full"
              >
                Try the Playground
              </Link>
            </div>
          </nav>
        </div>
      )}
    </>
  );
}

function OrchestrationLogo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none">
      {/* Connection lines */}
      <line x1="20" y1="30" x2="50" y2="50" stroke="#E25822" strokeWidth="1.5" opacity="0.4" />
      <line x1="35" y1="15" x2="50" y2="50" stroke="#E25822" strokeWidth="1.5" opacity="0.4" />
      <line x1="50" y1="10" x2="50" y2="50" stroke="#E25822" strokeWidth="1.5" opacity="0.4" />
      <line x1="65" y1="15" x2="50" y2="50" stroke="#E25822" strokeWidth="1.5" opacity="0.4" />
      <line x1="80" y1="30" x2="50" y2="50" stroke="#E25822" strokeWidth="1.5" opacity="0.4" />

      {/* Model nodes */}
      <circle cx="20" cy="30" r="6" fill="#E8D5C4" />
      <circle cx="35" cy="15" r="6" fill="#D4A574" />
      <circle cx="50" cy="10" r="6" fill="#C97B50" />
      <circle cx="65" cy="15" r="6" fill="#D4A574" />
      <circle cx="80" cy="30" r="6" fill="#E8D5C4" />

      {/* Central hub */}
      <circle cx="50" cy="50" r="10" fill="#E25822" />
    </svg>
  );
}