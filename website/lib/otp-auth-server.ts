import crypto from 'crypto';
import { getEmailDeliveryStatus, sendOtpEmail } from '@/lib/email';
import { createAppAuthToken } from '@/lib/app-auth';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getSupabaseAdminClient } from '@/lib/supabase-server';

export type OtpPurpose = 'signin' | 'signup';
const TTL_SECONDS = 10 * 60;

type Challenge = { email: string; codeHash: string; purpose: OtpPurpose; name?: string; nonce: string; exp: number };

function secret() { return process.env.OTP_SECRET || process.env.APP_AUTH_SECRET || process.env.TEMUCLAUDE_MASTER_KEY || ''; }
function normalizeEmail(value: unknown) { return typeof value === 'string' ? value.trim().toLowerCase() : ''; }
function digest(value: string) { return crypto.createHash('sha256').update(value).digest('hex'); }
function signature(payload: string) { const key = secret(); if (!key) throw new Error('OTP signing is not configured.'); return crypto.createHmac('sha256', key).update(payload).digest('base64url'); }

function createChallenge(value: Challenge) {
  const payload = Buffer.from(JSON.stringify(value)).toString('base64url');
  return `${payload}.${signature(payload)}`;
}

function readChallenge(token: unknown): Challenge | null {
  if (typeof token !== 'string') return null;
  const [payload, received] = token.split('.');
  if (!payload || !received) return null;
  const expected = signature(payload);
  if (received.length !== expected.length || !crypto.timingSafeEqual(Buffer.from(received), Buffer.from(expected))) return null;
  try {
    const challenge = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8')) as Challenge;
    return challenge.email && challenge.codeHash && challenge.nonce && challenge.exp >= Math.floor(Date.now() / 1000) ? challenge : null;
  } catch { return null; }
}

async function provisionPasswordUser(email: string, password: string | undefined, name: string) {
  if (!password || !process.env.NEXT_PUBLIC_SUPABASE_URL || !(process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY)) return;
  const { error } = await getSupabaseAdminClient().auth.admin.createUser({ email, password, email_confirm: true, user_metadata: { name, full_name: name } });
  if (error && !/already|registered|exists/i.test(error.message)) throw error;
}

export async function startOtp(input: { email: unknown; name: unknown; purpose: OtpPurpose }) {
  const email = normalizeEmail(input.email);
  if (!email || !email.includes('@')) throw new Error('Valid email is required.');
  if (!secret() || !getEmailDeliveryStatus().ready) throw new Error('Email verification is temporarily unavailable.');
  const code = String(crypto.randomInt(100000, 1000000));
  const nonce = crypto.randomBytes(16).toString('hex');
  const name = typeof input.name === 'string' ? input.name.trim().slice(0, 120) : undefined;
  const challenge = createChallenge({ email, purpose: input.purpose, name, nonce, codeHash: digest(`${email}:${code}:${nonce}`), exp: Math.floor(Date.now() / 1000) + TTL_SECONDS });
  const delivery = await sendOtpEmail(email, code, input.purpose);
  if (!delivery.success) throw new Error('Could not send verification code.');
  return { challenge, expiresIn: TTL_SECONDS };
}

export async function verifyOtp(input: { email: unknown; code: unknown; challenge: unknown; password: unknown; name: unknown; purpose: OtpPurpose }) {
  const email = normalizeEmail(input.email);
  const challenge = readChallenge(input.challenge);
  const code = typeof input.code === 'string' ? input.code.trim() : '';
  if (!email || !challenge || challenge.email !== email || challenge.purpose !== input.purpose || !/^\d{6}$/.test(code) || digest(`${email}:${code}:${challenge.nonce}`) !== challenge.codeHash) throw new Error('Invalid or expired verification challenge.');
  const password = typeof input.password === 'string' ? input.password : undefined;
  if (input.purpose === 'signup' && (!password || password.length < 6)) throw new Error('Password must be at least 6 characters.');
  const name = (typeof input.name === 'string' && input.name.trim()) || challenge.name || email.split('@')[0].replace(/[._-]+/g, ' ');
  await provisionPasswordUser(email, input.purpose === 'signup' ? password : undefined, name);
  const user = await getOrCreateUserByEmailAsync(email, name);
  return { id: user.id, email: user.email, name, provider: 'email', providers: ['email'], avatarInitials: name.split(/\s+/).slice(0, 2).map((part) => part[0]?.toUpperCase() || '').join(''), signedInAt: Date.now(), accessToken: createAppAuthToken({ id: user.id, email: user.email, name }) };
}
