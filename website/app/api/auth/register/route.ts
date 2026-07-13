import { NextRequest, NextResponse } from 'next/server';
import { createAppAuthToken } from '@/lib/app-auth';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getSupabaseAdminClient } from '@/lib/supabase-server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

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
    const email = typeof body.email === 'string' ? body.email.trim().toLowerCase() : '';
    const password = typeof body.password === 'string' ? body.password : '';
    const name = typeof body.name === 'string' ? body.name.trim() : '';

    if (!email || !email.includes('@')) {
      return NextResponse.json({ error: 'Valid email is required.' }, { status: 400 });
    }

    if (!password || password.length < 6) {
      return NextResponse.json({ error: 'Password must be at least 6 characters.' }, { status: 400 });
    }

    const displayName = name || email.split('@')[0].replace(/[._-]+/g, ' ');
    await ensureSupabasePasswordUser(email, password, displayName);
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
  } catch (error) {
    console.error('[AUTH] Registration error:', error);
    return NextResponse.json({ error: 'Registration failed.' }, { status: 500 });
  }
}
