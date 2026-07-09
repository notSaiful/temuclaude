'use client';

import { createClient, type Session, type SupabaseClient, type User } from '@supabase/supabase-js';

export type AuthProvider = 'email' | 'google' | 'github';
export type OAuthProvider = Extract<AuthProvider, 'google' | 'github'>;

export type LocalSession = {
  id: string;
  email: string;
  name: string;
  provider: AuthProvider;
  providers: AuthProvider[];
  avatarInitials: string;
  signedInAt: number;
};

export const AUTH_EVENT = 'temuclaude-auth-change';
const LOCAL_SESSION_KEY = 'temuclaude_local_auth_session';
const LOCAL_ACCOUNTS_KEY = 'temuclaude_local_auth_accounts';

let browserClient: SupabaseClient | null = null;

function initialsFrom(nameOrEmail: string) {
  const base = nameOrEmail.split('@')[0].replace(/[._-]+/g, ' ').trim() || 'User';
  return base
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || '')
    .join('');
}

function getPublicSupabaseConfig() {
  return {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL,
    anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  };
}

export function isSupabaseConfigured() {
  const { url, anonKey } = getPublicSupabaseConfig();
  return Boolean(url && anonKey);
}

export function getSupabaseBrowserClient() {
  const { url, anonKey } = getPublicSupabaseConfig();
  if (!url || !anonKey) {
    throw new Error('Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.');
  }

  if (!browserClient) {
    browserClient = createClient(url, anonKey, {
      auth: {
        autoRefreshToken: true,
        detectSessionInUrl: true,
        persistSession: true,
      },
    });
  }

  return browserClient;
}

function providerFromUser(user: User): AuthProvider {
  const provider = user.app_metadata?.provider;
  if (provider === 'google' || provider === 'github') return provider;
  return 'email';
}

function providersFromUser(user: User): AuthProvider[] {
  const providers = Array.isArray(user.app_metadata?.providers) ? user.app_metadata.providers : [];
  const authProviders = providers.filter((provider): provider is AuthProvider =>
    provider === 'email' || provider === 'google' || provider === 'github'
  );
  return authProviders.length ? Array.from(new Set(authProviders)) : [providerFromUser(user)];
}

function nameFromUser(user: User) {
  const metadata = user.user_metadata || {};
  return (
    metadata.full_name ||
    metadata.name ||
    metadata.user_name ||
    metadata.preferred_username ||
    user.email?.split('@')[0]?.replace(/[._-]+/g, ' ') ||
    'TemuClaude User'
  );
}

function toLocalSession(session: Session): LocalSession {
  const name = nameFromUser(session.user);
  return {
    id: session.user.id,
    email: session.user.email || '',
    name,
    provider: providerFromUser(session.user),
    providers: providersFromUser(session.user),
    avatarInitials: initialsFrom(name || session.user.email || 'User'),
    signedInAt: session.user.last_sign_in_at
      ? new Date(session.user.last_sign_in_at).getTime()
      : Date.now(),
  };
}

function emitAuthEvent() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(AUTH_EVENT));
  }
}

function clearSupabaseAuthStorage() {
  if (typeof window === 'undefined') return;

  for (let i = window.localStorage.length - 1; i >= 0; i -= 1) {
    const key = window.localStorage.key(i);
    if (key?.startsWith('sb-') && key.endsWith('-auth-token')) {
      window.localStorage.removeItem(key);
    }
  }
}

function getLocalAccounts(): Record<string, { email: string; password: string; name: string }> {
  if (typeof window === 'undefined') return {};

  try {
    return JSON.parse(window.localStorage.getItem(LOCAL_ACCOUNTS_KEY) || '{}');
  } catch {
    window.localStorage.removeItem(LOCAL_ACCOUNTS_KEY);
    return {};
  }
}

function saveLocalAccounts(accounts: Record<string, { email: string; password: string; name: string }>) {
  window.localStorage.setItem(LOCAL_ACCOUNTS_KEY, JSON.stringify(accounts));
}

function saveLocalSession(session: LocalSession) {
  window.localStorage.setItem(LOCAL_SESSION_KEY, JSON.stringify(session));
  emitAuthEvent();
}

function getLocalSession(): LocalSession | null {
  if (typeof window === 'undefined') return null;

  const raw = window.localStorage.getItem(LOCAL_SESSION_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as LocalSession;
  } catch {
    window.localStorage.removeItem(LOCAL_SESSION_KEY);
    return null;
  }
}

function createLocalSession(params: { email: string; name?: string; provider: AuthProvider }): LocalSession {
  const email = params.email.trim().toLowerCase();
  const name = params.name?.trim() || email.split('@')[0].replace(/[._-]+/g, ' ');

  return {
    id: `local_${params.provider}_${email}`,
    email,
    name,
    provider: params.provider,
    providers: [params.provider],
    avatarInitials: initialsFrom(name || email),
    signedInAt: Date.now(),
  };
}

function safeReturnTo(returnTo = '/dashboard') {
  return returnTo.startsWith('/') ? returnTo : '/dashboard';
}

function authRedirectUrl(returnTo?: string) {
  const url = new URL('/auth/callback', window.location.origin);
  url.searchParams.set('returnTo', safeReturnTo(returnTo));
  return url.toString();
}

export function sanitizeReturnTo(returnTo?: string | null) {
  return safeReturnTo(returnTo || '/dashboard');
}

export async function getStoredSession(): Promise<LocalSession | null> {
  if (!isSupabaseConfigured()) return getLocalSession();

  const supabase = getSupabaseBrowserClient();
  const { data, error } = await supabase.auth.getSession();
  if (error || !data.session) return null;
  return toLocalSession(data.session);
}

export async function getAccessToken(): Promise<string | null> {
  if (!isSupabaseConfigured()) {
    const session = getLocalSession();
    return session ? `local:${btoa(JSON.stringify({ id: session.id, email: session.email, name: session.name }))}` : null;
  }

  const supabase = getSupabaseBrowserClient();
  const { data, error } = await supabase.auth.getSession();
  if (error || !data.session) return null;
  return data.session.access_token;
}

export async function exchangeCodeForSession(code: string) {
  const supabase = getSupabaseBrowserClient();
  const { data, error } = await supabase.auth.exchangeCodeForSession(code);
  if (error) throw error;
  if (!data.session) return null;
  emitAuthEvent();
  return toLocalSession(data.session);
}

export function onAuthSessionChange(callback: (session: LocalSession | null) => void) {
  if (!isSupabaseConfigured()) {
    const syncLocalSession = () => callback(getLocalSession());
    window.addEventListener(AUTH_EVENT, syncLocalSession);
    return () => window.removeEventListener(AUTH_EVENT, syncLocalSession);
  }

  const supabase = getSupabaseBrowserClient();
  const { data } = supabase.auth.onAuthStateChange((_event, session) => {
    callback(session ? toLocalSession(session) : null);
    emitAuthEvent();
  });

  return () => data.subscription.unsubscribe();
}

export async function signInWithEmail(params: { email: string; password: string }) {
  if (!isSupabaseConfigured()) {
    const email = params.email.trim().toLowerCase();
    const account = getLocalAccounts()[email];
    if (!account || account.password !== params.password) {
      throw new Error('No local account found for this email and password. Create an account first.');
    }

    saveLocalSession(createLocalSession({ email, name: account.name, provider: 'email' }));
    return;
  }

  const supabase = getSupabaseBrowserClient();
  const { error } = await supabase.auth.signInWithPassword({
    email: params.email.trim().toLowerCase(),
    password: params.password,
  });
  if (error) throw error;
  emitAuthEvent();
}

export async function signUpWithEmail(params: { email: string; password: string; name?: string; returnTo?: string }) {
  if (!isSupabaseConfigured()) {
    const email = params.email.trim().toLowerCase();
    if (!params.password || params.password.length < 6) {
      throw new Error('Password must be at least 6 characters.');
    }

    const accounts = getLocalAccounts();
    const name = params.name?.trim() || email.split('@')[0].replace(/[._-]+/g, ' ');
    accounts[email] = { email, password: params.password, name };
    saveLocalAccounts(accounts);
    saveLocalSession(createLocalSession({ email, name, provider: 'email' }));
    return;
  }

  const supabase = getSupabaseBrowserClient();
  const { error } = await supabase.auth.signUp({
    email: params.email.trim().toLowerCase(),
    password: params.password,
    options: {
      data: {
        full_name: params.name?.trim() || undefined,
        name: params.name?.trim() || undefined,
      },
      emailRedirectTo: authRedirectUrl(params.returnTo),
    },
  });
  if (error) throw error;
  emitAuthEvent();
}

export async function signInWithOAuth(provider: OAuthProvider, returnTo?: string) {
  if (!isSupabaseConfigured()) {
    const name = provider === 'google' ? 'Google Local User' : 'GitHub Local User';
    const email = provider === 'google' ? 'google.local@temuclaude.local' : 'github.local@temuclaude.local';
    saveLocalSession(createLocalSession({ email, name, provider }));
    window.location.assign(sanitizeReturnTo(returnTo));
    return;
  }

  const supabase = getSupabaseBrowserClient();
  const { error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: authRedirectUrl(returnTo),
      queryParams: {
        prompt: 'consent',
      },
    },
  });
  if (error) throw error;
}

export async function signOut() {
  if (!isSupabaseConfigured()) {
    window.localStorage.removeItem(LOCAL_SESSION_KEY);
    emitAuthEvent();
    return;
  }

  const supabase = getSupabaseBrowserClient();
  await Promise.race([
    supabase.auth.signOut({ scope: 'local' }),
    new Promise((resolve) => setTimeout(resolve, 1500)),
  ]);
  clearSupabaseAuthStorage();
  emitAuthEvent();
}

export async function syncAuthenticatedUser() {
  const token = await getAccessToken();
  if (!token) return null;

  const res = await fetch('/api/auth/sync', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) return null;
  return res.json();
}

export async function sendOtp(email: string, returnTo?: string) {
  if (!isSupabaseConfigured()) {
    console.log(`Mock OTP sent to: ${email}`);
    return;
  }

  const supabase = getSupabaseBrowserClient();
  const { error } = await supabase.auth.signInWithOtp({
    email: email.trim().toLowerCase(),
    options: {
      emailRedirectTo: authRedirectUrl(returnTo),
      shouldCreateUser: true,
    },
  });
  if (error) throw error;
}

export async function verifyOtp(email: string, token: string, type: 'email' | 'signup' = 'email') {
  if (!isSupabaseConfigured()) {
    if (token !== '123456') {
      throw new Error('Invalid verification code. Use "123456" for mock sign in.');
    }
    saveLocalSession(createLocalSession({ email, name: email.split('@')[0], provider: 'email' }));
    return;
  }

  const supabase = getSupabaseBrowserClient();
  const { error } = await supabase.auth.verifyOtp({
    email: email.trim().toLowerCase(),
    token: token.trim(),
    type,
  });
  if (error) throw error;
  emitAuthEvent();
}
