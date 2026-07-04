// Create a new API key for the authenticated user
// POST /api/keys
// Body: { email, name? }
// Returns: { key, id } — key is only shown once

import { NextRequest, NextResponse } from 'next/server';
import { getUserByEmail, createApiKey, listApiKeys, revokeApiKey } from '@/lib/db';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

// POST: Create new API key
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, name } = body;

    if (!email) {
      return NextResponse.json({ error: 'Email required' }, { status: 400 });
    }

    const user = getUserByEmail(email);
    if (!user) {
      return NextResponse.json({ error: 'User not found. Subscribe to a plan first.' }, { status: 404 });
    }

    if (user.plan === 'free') {
      return NextResponse.json({ error: 'Upgrade to Pro or Enterprise to get API access' }, { status: 403 });
    }

    const result = createApiKey(user.id, name || 'default');

    return NextResponse.json({
      key: result.key,
      id: result.id,
      message: 'Save this key securely. It will not be shown again.',
    });
  } catch (error: any) {
    console.error('Create API key error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// GET: List API keys for a user
export async function GET(req: NextRequest) {
  try {
    const email = req.nextUrl.searchParams.get('email');
    if (!email) {
      return NextResponse.json({ error: 'Email required' }, { status: 400 });
    }

    const user = getUserByEmail(email);
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    const keys = listApiKeys(user.id);
    return NextResponse.json({ keys });
  } catch (error: any) {
    console.error('List API keys error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// DELETE: Revoke an API key
export async function DELETE(req: NextRequest) {
  try {
    const body = await req.json();
    const { keyId, email } = body;

    if (!keyId || !email) {
      return NextResponse.json({ error: 'keyId and email required' }, { status: 400 });
    }

    const user = getUserByEmail(email);
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    revokeApiKey(keyId);
    return NextResponse.json({ revoked: true });
  } catch (error: any) {
    console.error('Revoke API key error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}