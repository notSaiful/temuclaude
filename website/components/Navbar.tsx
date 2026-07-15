'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { getStoredSession, isSupabaseConfigured, onAuthSessionChange, signOut, type LocalSession } from '@/lib/auth';

// Keep every desktop and mobile product link in this one list. Account actions
// deliberately use the same text-link treatment, so a second CTA cannot drift
// into the header during future releases.
const primaryNavItems = [
  { label: 'Models', href: '/models' },
  { label: 'Playground', href: '/playground' },
  { label: 'Docs', href: '/docs' },
  { label: 'Pricing', href: '/pricing' },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [session, setSession] = useState<LocalSession | null>(null);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    let mounted = true;
    let unsubscribe: (() => void) | undefined;

    const syncSession = async () => {
      if (!isSupabaseConfigured()) {
        setSession(null);
        return;
      }

      try {
        const stored = await getStoredSession();
        if (mounted) setSession(stored);
      } catch {
        if (mounted) setSession(null);
      }
    };

    syncSession();
    if (isSupabaseConfigured()) {
      unsubscribe = onAuthSessionChange((nextSession) => {
        if (mounted) setSession(nextSession);
      });
    }

    return () => {
      mounted = false;
      unsubscribe?.();
    };
  }, []);

  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  const handleSignOut = async () => {
    await signOut().catch(() => undefined);
    setMobileOpen(false);
    if (pathname?.startsWith('/dashboard') || pathname?.startsWith('/playground')) {
      router.push('/login');
    }
  };

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
            {/* TemuClaude spark mark */}
            <svg width="28" height="28" viewBox="0 0 100 100" className="shrink-0" aria-hidden="true">
              <circle cx="50" cy="50" r="11" fill="#E25822"/>
              <line x1="50" y1="50" x2="50" y2="10" stroke="#E25822" strokeWidth="4.5" strokeLinecap="round"/>
              <line x1="50" y1="50" x2="79" y2="21" stroke="#E25822" strokeWidth="4.5" strokeLinecap="round"/>
              <line x1="50" y1="50" x2="90" y2="50" stroke="#E25822" strokeWidth="4.5" strokeLinecap="round"/>
              <line x1="50" y1="50" x2="79" y2="79" stroke="#E25822" strokeWidth="4.5" strokeLinecap="round"/>
              <line x1="50" y1="50" x2="50" y2="90" stroke="#E25822" strokeWidth="4.5" strokeLinecap="round"/>
              <line x1="50" y1="50" x2="21" y2="79" stroke="#E25822" strokeWidth="4.5" strokeLinecap="round"/>
              <line x1="50" y1="50" x2="10" y2="50" stroke="#E25822" strokeWidth="4.5" strokeLinecap="round"/>
              <line x1="50" y1="50" x2="21" y2="21" stroke="#E25822" strokeWidth="4.5" strokeLinecap="round"/>
            </svg>
            <span className="text-lg font-semibold tracking-tight text-text-primary">
              TemuClaude
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-8">
            {primaryNavItems.map((item) => (
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
            ))}
          </div>

          {/* Desktop account navigation */}
          <div className="hidden md:flex items-center gap-8">
            {session ? (
              <>
                <Link
                  href="/dashboard"
                  className={`nav-link ${pathname?.startsWith('/dashboard') ? 'nav-link-active' : ''}`}
                  aria-current={pathname?.startsWith('/dashboard') ? 'page' : undefined}
                >
                  Dashboard
                </Link>
                <button
                  onClick={handleSignOut}
                  className="nav-link cursor-pointer border-0 bg-transparent p-0"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className={`nav-link ${pathname?.startsWith('/login') ? 'nav-link-active' : ''}`}
                  aria-current={pathname?.startsWith('/login') ? 'page' : undefined}
                >
                  Sign In
                </Link>
              </>
            )}
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
              {primaryNavItems.map((item) => (
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
              {session ? (
                <>
                  <Link
                    href="/dashboard"
                    onClick={() => setMobileOpen(false)}
                    className="btn-secondary mt-4 w-full text-center py-2.5 text-sm font-semibold"
                  >
                    Dashboard
                  </Link>
                  <button
                    onClick={handleSignOut}
                    className="btn-secondary mt-2 w-full py-2.5 text-sm font-semibold cursor-pointer"
                  >
                    Sign Out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    onClick={() => setMobileOpen(false)}
                    className="btn-secondary mt-4 w-full text-center py-2.5 text-sm font-semibold"
                  >
                    Sign In
                  </Link>
                </>
              )}
            </div>
          </nav>
        </div>
      )}
    </>
  );
}
