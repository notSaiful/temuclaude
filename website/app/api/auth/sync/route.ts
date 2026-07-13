import { NextRequest, NextResponse } from 'next/server';
import type { User as SupabaseUser } from '@supabase/supabase-js';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function getDisplayName(user: SupabaseUser) {
  const metadata = user.user_metadata || {};
  return (
    metadata.full_name ||
    metadata.name ||
    metadata.user_name ||
    metadata.preferred_username ||
    user.email?.split('@')[0]?.replace(/[._-]+/g, ' ')
  );
}

export async function POST(req: NextRequest) {
  const auth = await getAuthenticatedSupabaseUser(req);
  if ('error' in auth) {
    return NextResponse.json({ error: auth.error }, { status: auth.status });
  }

  const { user: supabaseUser } = auth;
  const email = supabaseUser.email?.trim().toLowerCase();
  if (!email) {
    return NextResponse.json({ error: 'Authenticated Supabase user has no email address' }, { status: 400 });
  }

  const user = await getOrCreateUserByEmailAsync(email, getDisplayName(supabaseUser));

  return NextResponse.json({ user });
}
