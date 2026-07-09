// Create a new API key for the authenticated user
// POST /api/keys
// Headers: Authorization: Bearer <supabase_access_token>
// Body: { name? }
// Returns: { key, id } — key is only shown once

import { NextRequest, NextResponse } from 'next/server';
import { createApiKeyAsync, getOrCreateUserByEmailAsync, listApiKeysAsync, revokeApiKeyAsync } from '@/lib/db';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

async function getAppUser(req: NextRequest) {
  const auth = await getAuthenticatedSupabaseUser(req);
  if ('error' in auth) {
    return { error: auth.error, status: auth.status } as const;
  }

  const { user: supabaseUser } = auth;
  const email = supabaseUser.email?.trim().toLowerCase();
  if (!email) {
    return { error: 'Authenticated Supabase user has no email address', status: 400 } as const;
  }

  const metadata = supabaseUser.user_metadata || {};
  const name =
    metadata.full_name ||
    metadata.name ||
    metadata.user_name ||
    metadata.preferred_username ||
    email.split('@')[0].replace(/[._-]+/g, ' ');

  return { user: await getOrCreateUserByEmailAsync(email, name) } as const;
}

// POST: Create new API key
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { name } = body;
    const auth = await getAppUser(req);
    if ('error' in auth) {
      return NextResponse.json({ error: auth.error }, { status: auth.status });
    }

    const user = auth.user;
    if (user.plan === 'free') {
      return NextResponse.json({ error: 'Upgrade to Developer, Pro, or Enterprise to get API access' }, { status: 403 });
    }

    const result = await createApiKeyAsync(user.id, name || 'default');

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
    const auth = await getAppUser(req);
    if ('error' in auth) {
      return NextResponse.json({ error: auth.error }, { status: auth.status });
    }

    const keys = await listApiKeysAsync(auth.user.id);
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
    const { keyId } = body;

    if (!keyId) {
      return NextResponse.json({ error: 'keyId required' }, { status: 400 });
    }

    const auth = await getAppUser(req);
    if ('error' in auth) {
      return NextResponse.json({ error: auth.error }, { status: auth.status });
    }

    const keyBelongsToUser = (await listApiKeysAsync(auth.user.id)).some((key) => key.id === keyId);
    if (!keyBelongsToUser) {
      return NextResponse.json({ error: 'API key not found' }, { status: 404 });
    }

    await revokeApiKeyAsync(keyId);
    return NextResponse.json({ revoked: true });
  } catch (error: any) {
    console.error('Revoke API key error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
