import { NextRequest, NextResponse } from 'next/server';
import { validateApiKeyAsync } from '@/lib/db';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const MODELS = [
  { id: 'temuclaude/temuclaude-pro', object: 'model', owned_by: 'temuclaude' },
  { id: 'temuclaude/temuclaude-lite', object: 'model', owned_by: 'temuclaude' },
];

export async function GET(request: NextRequest) {
  const apiKey = request.headers.get('authorization')?.replace(/^Bearer\s+/i, '') || request.headers.get('x-api-key') || '';
  if (!apiKey) return NextResponse.json({ error: { message: 'Missing API key', type: 'authentication_error' } }, { status: 401 });

  const masterKey = process.env.TEMUCLAUDE_MASTER_KEY;
  if (!masterKey || apiKey !== masterKey) {
    const valid = await validateApiKeyAsync(apiKey);
    if (!valid) return NextResponse.json({ error: { message: 'Invalid API key', type: 'authentication_error' } }, { status: 401 });
    if (valid.user.plan === 'free') {
      return NextResponse.json({ error: { message: 'API access requires a Developer, Pro, Max, or Enterprise plan.', type: 'permission_error' } }, { status: 403 });
    }
  }

  return NextResponse.json({ object: 'list', data: MODELS });
}
