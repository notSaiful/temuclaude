import { NextRequest, NextResponse } from 'next/server';
import { getOrCreateUserByEmailAsync } from '@/lib/db';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import { beginWorkspaceActionExecution, finishWorkspaceAction } from '@/lib/workspace';
import { createVercelDeployment } from '@/lib/vercel/deploy';
import { executeWorkspaceAction } from '@/lib/workspace-executor';
export const runtime = 'nodejs'; export const dynamic = 'force-dynamic';
type Context = { params: Promise<{ projectId: string; actionId: string }> };
export async function POST(req: NextRequest, context: Context) {
  const { projectId, actionId } = await context.params; let userId = ''; let started = false;
  try { const auth = await getAuthenticatedSupabaseUser(req); if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status }); const email = auth.user.email?.trim().toLowerCase(); if (!email) return NextResponse.json({ error: 'Authenticated user has no email address' }, { status: 400 }); const user = await getOrCreateUserByEmailAsync(email, String(auth.user.user_metadata?.full_name || email.split('@')[0])); userId = user.id; const action = await beginWorkspaceActionExecution({ userId, projectId, actionId }); started = true;
    if (action.action_type === 'deploy.preview' || action.action_type === 'deploy.production') { const p = action.requested_payload; if (typeof p.name !== 'string' || typeof p.repoId !== 'string' || typeof p.ref !== 'string') throw new Error('Deployment action requires name, repoId, and ref.'); const deployment = await createVercelDeployment({ name: p.name, gitSource: { type: 'github', repoId: p.repoId, ref: p.ref }, target: action.action_type === 'deploy.production' ? 'production' : undefined }); const completed = await finishWorkspaceAction({ userId, projectId, actionId, status: 'completed', details: { deployment } }); return NextResponse.json({ action: completed, deployment }); }
    const result = await executeWorkspaceAction({ action, userId, projectId }); const completed = await finishWorkspaceAction({ userId, projectId, actionId, status: 'completed', details: result }); return NextResponse.json({ action: completed, result });
  } catch (error) { const message = error instanceof Error ? error.message : 'Action execution failed.'; if (started && userId) await finishWorkspaceAction({ userId, projectId, actionId, status: 'failed', details: { error: message } }).catch(() => undefined); return NextResponse.json({ error: message }, { status: started ? 502 : 409 }); }
}
