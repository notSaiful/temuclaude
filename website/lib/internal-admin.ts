import crypto from 'crypto';
import { NextRequest } from 'next/server';

/**
 * Guard machine-control endpoints. These routes are for private operational
 * tooling only and must never accept a browser session as authority to execute
 * shell commands or mutate deployment queues.
 */
export function hasInternalAdminAccess(req: NextRequest): boolean {
  const expected = process.env.TEMUCLAUDE_INTERNAL_ADMIN_KEY || '';
  const supplied = req.headers.get('x-temuclaude-internal-key') || '';
  if (!expected || !supplied || expected.length !== supplied.length) return false;
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(supplied));
}
