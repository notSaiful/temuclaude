'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Navbar } from '@/components/Navbar';
import {
  exchangeCodeForSession,
  getStoredSession,
  isSupabaseConfigured,
  sanitizeReturnTo,
  syncAuthenticatedUser,
} from '@/lib/auth';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function waitForStoredSession() {
      for (let attempt = 0; attempt < 10; attempt += 1) {
        const session = await getStoredSession();
        if (session) return session;
        await new Promise((resolve) => setTimeout(resolve, 250));
      }
      return null;
    }

    async function finishAuth() {
      const returnTo = sanitizeReturnTo(searchParams.get('returnTo'));
      const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ''));
      const providerError =
        searchParams.get('error_description') ||
        searchParams.get('error') ||
        hashParams.get('error_description') ||
        hashParams.get('error');
      if (providerError) {
        setError(providerError);
        return;
      }

      if (!isSupabaseConfigured() && searchParams.get('code')) {
        setError('This authentication link was opened without Supabase configured. Go back to sign in and use local auth, or add Supabase credentials to enable hosted OAuth.');
        return;
      }

      try {
        const code = searchParams.get('code');
        const session = code ? await exchangeCodeForSession(code) : await waitForStoredSession();
        if (!session) {
          router.replace(`/login?returnTo=${encodeURIComponent(returnTo)}`);
          return;
        }

        await syncAuthenticatedUser();
        if (mounted) router.replace(returnTo);
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Authentication callback failed.');
        }
      }
    }

    finishAuth();

    return () => {
      mounted = false;
    };
  }, [router, searchParams]);

  return (
    <>
      <Navbar />
      <main className="min-h-screen pt-32 pb-24 px-6 flex items-center justify-center bg-bg-primary">
        <div className="card max-w-md w-full p-8 text-center">
          {error ? (
            <>
              <h1 className="text-2xl font-serif text-text-primary mb-3">Sign-in failed</h1>
              <p className="text-sm text-text-secondary mb-6">{error}</p>
              <Link href="/login" className="btn-accent justify-center">
                Back to Sign In
              </Link>
            </>
          ) : (
            <>
              <h1 className="text-2xl font-serif text-text-primary mb-3">Finishing sign in...</h1>
              <p className="text-sm text-text-secondary">
                We are securely connecting your account and redirecting you.
              </p>
            </>
          )}
        </div>
      </main>
    </>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <>
          <Navbar />
          <main className="min-h-screen pt-32 pb-24 px-6 flex items-center justify-center bg-bg-primary">
            <div className="card max-w-md w-full p-8 text-center">
              <h1 className="text-2xl font-serif text-text-primary mb-3">Finishing sign in...</h1>
              <p className="text-sm text-text-secondary">
                We are securely connecting your account and redirecting you.
              </p>
            </div>
          </main>
        </>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}
