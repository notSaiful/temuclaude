import crypto from 'crypto';
import { NextRequest, NextResponse } from 'next/server';
import { getEmailDeliveryStatus, sendOtpEmail } from '@/lib/email';
import { createAppAuthToken } from '@/lib/app-auth';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getSupabaseAdminClient } from '@/lib/supabase-server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const OTP_TTL_SECONDS = 10 * 60;
const OTP_START_WINDOW_MS = 10 * 60 * 1000;
const OTP_MAX_STARTS_PER_WINDOW = 5;
const otpStartBuckets = new Map<string, { count: number; resetAt: number }>();

interface OtpChallenge {
  email: string;
  codeHash: string;
  purpose: 'signin' | 'signup';
  name?: string;
  nonce: string;
  exp: number;
}

function getOtpSecret() {
  return process.env.OTP_SECRET || process.env.APP_AUTH_SECRET || process.env.TEMUCLAUDE_MASTER_KEY || '';
}

function normalizeEmail(email: string) {
  return email.trim().toLowerCase();
}

function hash(value: string) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function getClientIp(req: NextRequest) {
  return (
    req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ||
    req.headers.get('x-real-ip') ||
    'unknown'
  );
}

function checkOtpStartRateLimit(email: string, req: NextRequest) {
  const key = `${email}:${getClientIp(req)}`;
  const now = Date.now();
  const current = otpStartBuckets.get(key);

  if (!current || current.resetAt <= now) {
    otpStartBuckets.set(key, { count: 1, resetAt: now + OTP_START_WINDOW_MS });
    return true;
  }

  if (current.count >= OTP_MAX_STARTS_PER_WINDOW) {
    return false;
  }

  current.count += 1;
  return true;
}

function signPayload(payload: string) {
  const secret = getOtpSecret();
  if (!secret) throw new Error('OTP_SECRET, APP_AUTH_SECRET, or TEMUCLAUDE_MASTER_KEY must be configured.');
  return crypto.createHmac('sha256', secret).update(payload).digest('base64url');
}

function createChallenge(challenge: OtpChallenge) {
  const payload = Buffer.from(JSON.stringify(challenge)).toString('base64url');
  return `${payload}.${signPayload(payload)}`;
}

function verifyChallenge(challengeToken: string): OtpChallenge | null {
  const [payload, signature] = challengeToken.split('.');
  if (!payload || !signature) return null;

  const expected = signPayload(payload);
  if (signature.length !== expected.length) return null;
  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) return null;

  try {
    const challenge = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8')) as OtpChallenge;
    if (!challenge.email || !challenge.codeHash || challenge.exp < Math.floor(Date.now() / 1000)) return null;
    return challenge;
  } catch {
    return null;
  }
}

async function ensureSupabasePasswordUser(email: string, password?: string, name?: string) {
  if (!password || !process.env.NEXT_PUBLIC_SUPABASE_URL || !(process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY)) {
    return;
  }

  try {
    const admin = getSupabaseAdminClient();
    const { error } = await admin.auth.admin.createUser({
      email,
      password,
      email_confirm: true,
      user_metadata: {
        name,
        full_name: name,
      },
    });

    if (error && !/already|registered|exists/i.test(error.message)) {
      throw error;
    }
  } catch (error) {
    console.warn('[AUTH] Supabase password user provisioning skipped:', error instanceof Error ? error.message : error);
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const action = body.action as 'start' | 'verify';
    const email = typeof body.email === 'string' ? normalizeEmail(body.email) : '';
    const purpose = body.purpose === 'signup' ? 'signup' : 'signin';
    const name = typeof body.name === 'string' ? body.name.trim() : undefined;

    if (!email || !email.includes('@')) {
      return NextResponse.json({ error: 'Valid email is required.' }, { status: 400 });
    }

    if (action === 'start') {
      if (!getOtpSecret()) {
        return NextResponse.json(
          { error: 'Verification is temporarily unavailable. Please try again shortly.' },
          { status: 503 },
        );
      }

      if (!getEmailDeliveryStatus().ready) {
        return NextResponse.json(
          { error: 'Email delivery is temporarily unavailable. Please try again shortly.' },
          { status: 503 },
        );
      }

      if (!checkOtpStartRateLimit(email, req)) {
        return NextResponse.json(
          { error: 'Too many verification codes requested. Please wait a few minutes and try again.' },
          { status: 429 },
        );
      }

      const code = String(crypto.randomInt(100000, 1000000));
      const nonce = crypto.randomBytes(16).toString('hex');
      const challenge = createChallenge({
        email,
        purpose,
        name,
        nonce,
        codeHash: hash(`${email}:${code}:${nonce}`),
        exp: Math.floor(Date.now() / 1000) + OTP_TTL_SECONDS,
      });

      const result = await sendOtpEmail(email, code, purpose);
      if (!result.success) {
        const isConfigError = /configured|password|key/i.test(result.error || '');
        return NextResponse.json({
          error: isConfigError
            ? 'Email delivery is not configured. Please contact support.'
            : 'Could not send verification code. Please try again shortly.',
        }, { status: 500 });
      }

      return NextResponse.json({ success: true, challenge, expiresIn: OTP_TTL_SECONDS });
    }

    if (action === 'verify') {
      const code = typeof body.code === 'string' ? body.code.trim() : '';
      const challengeToken = typeof body.challenge === 'string' ? body.challenge : '';
      const password = typeof body.password === 'string' ? body.password : undefined;
      const challenge = verifyChallenge(challengeToken);

      if (!challenge || challenge.email !== email || challenge.purpose !== purpose) {
        return NextResponse.json({ error: 'Invalid or expired verification challenge.' }, { status: 400 });
      }

      if (!/^\d{6}$/.test(code) || hash(`${email}:${code}:${challenge.nonce}`) !== challenge.codeHash) {
        return NextResponse.json({ error: 'Invalid verification code.' }, { status: 400 });
      }

      if (purpose === 'signup' && (!password || password.length < 6)) {
        return NextResponse.json({ error: 'Password must be at least 6 characters.' }, { status: 400 });
      }

      const displayName = name || challenge.name || email.split('@')[0].replace(/[._-]+/g, ' ');
      await ensureSupabasePasswordUser(email, purpose === 'signup' ? password : undefined, displayName);
      const user = await getOrCreateUserByEmailAsync(email, displayName);
      const token = createAppAuthToken({ id: user.id, email: user.email, name: displayName });

      return NextResponse.json({
        success: true,
        session: {
          id: user.id,
          email: user.email,
          name: displayName,
          provider: 'email',
          providers: ['email'],
          avatarInitials: String(displayName)
            .split(/\s+/)
            .slice(0, 2)
            .map((part: string) => part[0]?.toUpperCase() || '')
            .join(''),
          signedInAt: Date.now(),
          accessToken: token,
        },
      });
    }

    return NextResponse.json({ error: 'Invalid OTP action.' }, { status: 400 });
  } catch (error) {
    console.error('[AUTH] OTP error:', error);
    return NextResponse.json({ error: 'OTP request failed.' }, { status: 500 });
  }
}
