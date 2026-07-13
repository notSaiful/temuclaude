import { NextRequest } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import { createMediaJob, inferMediaKind, MediaJobError } from '@/lib/media-jobs';

export const runtime = 'nodejs';
export const maxDuration = 60;

export async function POST(request: NextRequest) {
  const auth = await getAuthenticatedSupabaseUser(request);
  if ('error' in auth) return Response.json({ error: auth.error }, { status: auth.status });
  const email = auth.user.email?.trim().toLowerCase();
  if (!email) return Response.json({ error: 'Authenticated user has no email address' }, { status: 400 });
  try {
    const body = await request.json() as Record<string, unknown>;
    const prompt = body.prompt;
    if (typeof prompt !== 'string') {
      return Response.json({ error: 'prompt is required.' }, { status: 400 });
    }
    const kind = inferMediaKind(prompt);
    if (!kind) return Response.json({ error: 'This prompt does not request a supported media output.' }, { status: 400 });
    const user = await getOrCreateUserByEmailAsync(email, auth.user.user_metadata?.name as string | undefined);
    const enabledPlans = (process.env.MEDIA_ENABLED_PLANS || 'developer,pro,max,enterprise').split(',').map((plan) => plan.trim());
    if (!enabledPlans.includes(user.plan)) {
      return Response.json({ error: 'Media generation is available on Developer, Pro, Max, and Enterprise plans.' }, { status: 403 });
    }
    const job = await createMediaJob({
      userId: user.id,
      kind,
      prompt,
      lyrics: typeof body.lyrics === 'string' ? body.lyrics : undefined,
      voice: typeof body.voice === 'string' ? body.voice : undefined,
    });
    return Response.json({ job }, { status: 201 });
  } catch (error) {
    if (error instanceof MediaJobError) return Response.json({ error: error.message, code: error.code }, { status: error.status });
    return Response.json({ error: 'Unable to create media job.' }, { status: 500 });
  }
}
