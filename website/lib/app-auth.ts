import crypto from 'crypto';

export interface AppAuthPayload {
  id: string;
  email: string;
  name?: string;
  exp: number;
}

function getAppAuthSecret() {
  return process.env.APP_AUTH_SECRET || process.env.TEMUCLAUDE_MASTER_KEY || '';
}

function base64url(input: string | Buffer) {
  return Buffer.from(input).toString('base64url');
}

function signPayload(payload: string, secret: string) {
  return crypto.createHmac('sha256', secret).update(payload).digest('base64url');
}

export function createAppAuthToken(payload: Omit<AppAuthPayload, 'exp'>, ttlSeconds = 60 * 60 * 24 * 30) {
  const secret = getAppAuthSecret();
  if (!secret) {
    throw new Error('APP_AUTH_SECRET or TEMUCLAUDE_MASTER_KEY must be configured.');
  }

  const encodedPayload = base64url(JSON.stringify({
    ...payload,
    exp: Math.floor(Date.now() / 1000) + ttlSeconds,
  }));
  const signature = signPayload(encodedPayload, secret);
  return `app:${encodedPayload}.${signature}`;
}

export function verifyAppAuthToken(token: string): AppAuthPayload | null {
  const secret = getAppAuthSecret();
  if (!secret || !token.startsWith('app:')) return null;

  const raw = token.slice('app:'.length);
  const [encodedPayload, signature] = raw.split('.');
  if (!encodedPayload || !signature) return null;

  const expected = signPayload(encodedPayload, secret);
  if (signature.length !== expected.length) return null;
  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return null;
  }

  try {
    const payload = JSON.parse(Buffer.from(encodedPayload, 'base64url').toString('utf8')) as AppAuthPayload;
    if (!payload.email || !payload.id || payload.exp < Math.floor(Date.now() / 1000)) {
      return null;
    }
    return payload;
  } catch {
    return null;
  }
}
