import { createClient, type SupabaseClient, type User as SupabaseUser } from '@supabase/supabase-js';
import type { NextRequest } from 'next/server';

type AuthenticatedUserResult =
  | { user: SupabaseUser; token: string; error?: never; status?: never }
  | { error: string; status: number; user?: never; token?: never };

let serverClient: SupabaseClient | null = null;
let adminClient: SupabaseClient | null = null;

function getSupabaseServerClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!url || !anonKey) {
    throw new Error('Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.');
  }

  if (!serverClient) {
    serverClient = createClient(url, anonKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    });
  }

  return serverClient;
}

export function getSupabaseAdminClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const secretKey = process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !secretKey) {
    throw new Error('Supabase admin is not configured. Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SECRET_KEY.');
  }

  if (!adminClient) {
    adminClient = createClient(url, secretKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    });
  }

  return adminClient;
}

export async function getAuthenticatedSupabaseUser(req: NextRequest): Promise<AuthenticatedUserResult> {
  const authHeader = req.headers.get('authorization');
  const token = authHeader?.replace(/^Bearer\s+/i, '').trim();

  if (!token) {
    return { error: 'Missing Supabase access token', status: 401 };
  }

  if (token.startsWith('local:')) {
    if (process.env.NODE_ENV === 'production') {
      return { error: 'Local auth tokens are not accepted in production', status: 401 };
    }

    try {
      const encodedPayload = token.slice('local:'.length);
      const payload = JSON.parse(Buffer.from(encodedPayload, 'base64').toString('utf8')) as {
        id: string;
        email: string;
        name?: string;
      };

      return {
        token,
        user: {
          id: payload.id,
          aud: 'authenticated',
          role: 'authenticated',
          email: payload.email,
          app_metadata: { provider: 'email', providers: ['email'] },
          user_metadata: { name: payload.name, full_name: payload.name },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        } as SupabaseUser,
      };
    } catch {
      return { error: 'Invalid local auth token', status: 401 };
    }
  }

  try {
    const supabase = getSupabaseServerClient();
    const { data, error } = await supabase.auth.getUser(token);
    if (error || !data.user) {
      return { error: 'Invalid Supabase access token', status: 401 };
    }

    return { user: data.user, token };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Supabase authentication failed';
    return { error: message, status: 500 };
  }
}
