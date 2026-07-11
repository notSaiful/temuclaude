'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Navbar } from '@/components/Navbar';
import {
  getStoredSession,
  onAuthSessionChange,
  signInWithEmail,
  signInWithOAuth,
  signUpWithEmail,
  syncAuthenticatedUser,
  verifyOtp,
  type OAuthProvider,
} from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [returnTo, setReturnTo] = useState('/dashboard');

  const handleModeChange = (newMode: 'signin' | 'signup') => {
    setMode(newMode);
    setError(null);
    setNotice(null);
    setOtpSent(false);
    setOtpCode('');
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const nextReturnTo = params.get('returnTo') || '/dashboard';
    setReturnTo(nextReturnTo);

    let mounted = true;

    getStoredSession()
      .then(async (session) => {
        if (!mounted || !session) return;
        await syncAuthenticatedUser();
        router.replace(nextReturnTo);
      })
      .catch((err) => {
        if (mounted) setError(err instanceof Error ? err.message : 'Could not check the current session.');
      });

    const unsubscribe = onAuthSessionChange(async (session) => {
      if (!mounted || !session) return;
      await syncAuthenticatedUser();
      router.replace(nextReturnTo);
    });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Please enter your email.');
      return;
    }

    setLoading(true);
    setError(null);
    setNotice(null);

    try {
      if (mode === 'signup') {
        if (!password.trim() || password.length < 6) {
          setError('Password must be at least 6 characters.');
          setLoading(false);
          return;
        }
        if (!otpSent) {
          await signUpWithEmail({ email, password, name, returnTo });
          setOtpSent(true);
          setNotice(`We sent a verification code to ${email.trim().toLowerCase()}.`);
          return;
        }

        if (!/^\d{6}$/.test(otpCode.trim())) {
          setError('Enter the 6-digit verification code from your email.');
          return;
        }

        await verifyOtp(email, otpCode, 'signup', { password, name });
        const session = await getStoredSession();
        if (session) {
          await syncAuthenticatedUser();
          router.push(returnTo);
          return;
        }
      } else {
        if (!password.trim()) {
          setError('Please enter your password.');
          setLoading(false);
          return;
        }
        await signInWithEmail({ email, password });
        const session = await getStoredSession();
        if (session) {
          await syncAuthenticatedUser();
          router.push(returnTo);
          return;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = async (provider: OAuthProvider) => {
    setLoading(true);
    setError(null);
    setNotice(null);

    try {
      await signInWithOAuth(provider, returnTo);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Could not start ${provider} sign in.`);
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="min-h-screen pt-28 px-6 bg-bg-primary" id="main-content">
        <div className="container-max max-w-md mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-serif text-text-primary mb-2">
              {mode === 'signup' ? 'Create your account' : 'Welcome back'}
            </h1>
            <p className="text-sm text-text-secondary">
              {mode === 'signup' ? 'Get started with TemuClaude' : 'Sign in to your developer dashboard'}
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-accent-fig/10 border border-accent-fig/20 text-accent-fig text-xs rounded-sm" role="alert">
              {error}
            </div>
          )}

          {notice && (
            <div className="mb-4 p-3 bg-accent-olive/10 border border-accent-olive/20 text-accent-olive text-xs rounded-sm" role="status">
              {notice}
            </div>
          )}

          <div className="grid grid-cols-2 gap-2 mb-6 rounded-md bg-bg-secondary p-1">
            <button
              type="button"
              onClick={() => handleModeChange('signin')}
              className={`py-2 text-xs font-semibold rounded-sm transition-colors ${
                mode === 'signin' ? 'bg-white text-text-primary shadow-sm' : 'text-text-secondary'
              }`}
              disabled={loading}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => handleModeChange('signup')}
              className={`py-2 text-xs font-semibold rounded-sm transition-colors ${
                mode === 'signup' ? 'bg-white text-text-primary shadow-sm' : 'text-text-secondary'
              }`}
              disabled={loading}
            >
              Create Account
            </button>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            {mode === 'signup' && (
              <div>
                <label htmlFor="name" className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
                  Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ada Lovelace"
                  className="input w-full"
                  disabled={loading}
                />
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@example.com"
                className="input w-full"
                disabled={loading}
              />
            </div>

            {mode === 'signup' && otpSent && (
              <div>
                <label htmlFor="otp" className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
                  Verification Code
                </label>
                <input
                  id="otp"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="123456"
                  className="input w-full tracking-[0.35em]"
                  disabled={loading}
                />
              </div>
            )}

            <div>
              <label htmlFor="password" className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="input w-full"
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-accent w-full justify-center !py-3 font-semibold disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {loading
                ? 'Working...'
                : mode === 'signup'
                ? otpSent
                  ? 'Verify and Create Account'
                  : 'Send Verification Code'
                : 'Sign In'}
            </button>
          </form>

          <div className="relative my-6 text-center">
            <hr className="border-border-default" />
            <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-bg-primary px-3 text-xs text-text-muted">
              or continue with
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-6">
            <button
              onClick={() => handleOAuth('google')}
              disabled={loading}
              className="btn-secondary !py-2.5 justify-center text-xs font-medium cursor-pointer"
            >
              <svg className="w-4 h-4 mr-1.5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12.24 10.285V14.4h6.887c-.648 2.41-2.519 4.114-5.136 4.114-3.51 0-6.357-2.89-6.357-6.457 0-3.567 2.848-6.458 6.357-6.458 1.614 0 3.08.6 4.218 1.584l3.14-3.14C19.262 2.228 15.966 1 12.24 1 5.926 1 .8 6.126.8 12.457c0 6.332 5.126 11.458 11.44 11.458 7.37 0 11.96-5.177 11.96-12.182 0-.693-.06-1.393-.19-2.062l-11.77-.386z"/>
              </svg>
              Google
            </button>
            <button
              onClick={() => handleOAuth('github')}
              disabled={loading}
              className="btn-secondary !py-2.5 justify-center text-xs font-medium cursor-pointer"
            >
              <svg className="w-4 h-4 mr-1.5" viewBox="0 0 24 24" fill="currentColor">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.162 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
              </svg>
              GitHub
            </button>
          </div>

          <div className="text-center text-xs text-text-muted mt-6">
            By signing in, you agree to our <a href="/terms" className="hover:text-text-primary underline">Terms</a> and <a href="/privacy" className="hover:text-text-primary underline">Privacy Policy</a>.
          </div>
        </div>
      </main>
    </>
  );
}
