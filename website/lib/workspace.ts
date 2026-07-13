import crypto from 'crypto';
import { getSupabaseAdminClient } from '@/lib/supabase-server';

export type WorkspaceProfile = 'pro' | 'lite';

export type WorkspaceProject = {
  id: string;
  user_id: string;
  title: string;
  profile: WorkspaceProfile;
  status: 'active' | 'archived' | 'deleted';
  created_at: number;
  updated_at: number;
};

export type WorkspaceFile = {
  id: string;
  project_id: string;
  user_id: string;
  file_path: string;
  content: string;
  language: string | null;
  content_sha256: string;
  byte_size: number;
  created_at: number;
  updated_at: number;
};

export type WorkspaceActionType = 'agent.run' | 'file.write' | 'command.run' | 'package.install' | 'network.enable' | 'browser.run' | 'github.connect' | 'deploy.preview' | 'deploy.production';
export type WorkspaceActionStatus = 'requested' | 'approved' | 'rejected' | 'executing' | 'completed' | 'failed' | 'cancelled';
export type WorkspaceAction = { id: string; project_id: string; user_id: string; action_type: WorkspaceActionType; status: WorkspaceActionStatus; requested_payload: Record<string, unknown>; decision_payload: Record<string, unknown>; requested_at: number; decided_at: number | null; expires_at: number; created_at: number; updated_at: number };
const ACTION_TYPES: WorkspaceActionType[] = ['agent.run', 'file.write', 'command.run', 'package.install', 'network.enable', 'browser.run', 'github.connect', 'deploy.preview', 'deploy.production'];

const MAX_FILE_BYTES = 1_048_576;

function nowUnix() {
  return Math.floor(Date.now() / 1000);
}

function newId(prefix: string) {
  return `${prefix}_${crypto.randomBytes(16).toString('hex')}`;
}

function sha256(content: string) {
  return crypto.createHash('sha256').update(content, 'utf8').digest('hex');
}

function byteLength(content: string) {
  return Buffer.byteLength(content, 'utf8');
}

function mapProject(row: Record<string, unknown>): WorkspaceProject {
  return {
    id: String(row.id),
    user_id: String(row.user_id),
    title: String(row.title),
    profile: row.profile === 'lite' ? 'lite' : 'pro',
    status: row.status === 'archived' || row.status === 'deleted' ? row.status : 'active',
    created_at: Number(row.created_at),
    updated_at: Number(row.updated_at),
  };
}

function mapFile(row: Record<string, unknown>): WorkspaceFile {
  return {
    id: String(row.id),
    project_id: String(row.project_id),
    user_id: String(row.user_id),
    file_path: String(row.file_path),
    content: String(row.content),
    language: typeof row.language === 'string' ? row.language : null,
    content_sha256: String(row.content_sha256),
    byte_size: Number(row.byte_size),
    created_at: Number(row.created_at),
    updated_at: Number(row.updated_at),
  };
}

function mapAction(row: Record<string, unknown>): WorkspaceAction {
  return { id: String(row.id), project_id: String(row.project_id), user_id: String(row.user_id), action_type: row.action_type as WorkspaceActionType, status: row.status as WorkspaceActionStatus, requested_payload: (row.requested_payload || {}) as Record<string, unknown>, decision_payload: (row.decision_payload || {}) as Record<string, unknown>, requested_at: Number(row.requested_at), decided_at: row.decided_at === null ? null : Number(row.decided_at), expires_at: Number(row.expires_at), created_at: Number(row.created_at), updated_at: Number(row.updated_at) };
}

export async function listWorkspaceActions(userId: string, projectId: string): Promise<WorkspaceAction[]> {
  if (!await getWorkspaceProject(userId, projectId)) return [];
  const { data, error } = await getSupabaseAdminClient().from('temuclaude_project_actions').select('*').eq('project_id', projectId).eq('user_id', userId).order('created_at', { ascending: false }).limit(100);
  if (error) throw error;
  return (data || []).map((row) => mapAction(row as Record<string, unknown>));
}

export async function requestWorkspaceAction(input: { userId: string; projectId: string; actionType: WorkspaceActionType; payload?: Record<string, unknown>; expiresInSeconds?: number }): Promise<WorkspaceAction> {
  if (!ACTION_TYPES.includes(input.actionType)) throw new Error('Unsupported action type.');
  if (!await getWorkspaceProject(input.userId, input.projectId)) throw new Error('Project not found.');
  const now = nowUnix(); const expires = Math.max(60, Math.min(input.expiresInSeconds || 900, 3600));
  const row = { id: newId('action'), project_id: input.projectId, user_id: input.userId, action_type: input.actionType, status: 'requested', requested_payload: input.payload || {}, decision_payload: {}, requested_at: now, decided_at: null, expires_at: now + expires, created_at: now, updated_at: now };
  const { data, error } = await getSupabaseAdminClient().from('temuclaude_project_actions').insert(row).select('*').single();
  if (error) throw error;
  await recordWorkspaceEvent({ userId: input.userId, projectId: input.projectId, eventType: 'action.requested', summary: `Approval requested for ${input.actionType}`, details: { actionId: row.id } });
  return mapAction(data as Record<string, unknown>);
}

export async function decideWorkspaceAction(input: { userId: string; projectId: string; actionId: string; approve: boolean; reason?: string }): Promise<WorkspaceAction> {
  const client = getSupabaseAdminClient(); const now = nowUnix();
  const { data: current, error: fetchError } = await client.from('temuclaude_project_actions').select('*').eq('id', input.actionId).eq('project_id', input.projectId).eq('user_id', input.userId).maybeSingle();
  if (fetchError) throw fetchError;
  if (!current) throw new Error('Action not found.');
  if (current.status !== 'requested') throw new Error('Only requested actions may be decided.');
  if (Number(current.expires_at) <= now) throw new Error('Action approval has expired.');
  const status = input.approve ? 'approved' : 'rejected';
  const { data, error } = await client.from('temuclaude_project_actions').update({ status, decided_at: now, updated_at: now, decision_payload: { reason: input.reason?.slice(0, 500) || null } }).eq('id', input.actionId).eq('status', 'requested').select('*').single();
  if (error) throw error;
  await recordWorkspaceEvent({ userId: input.userId, projectId: input.projectId, eventType: `action.${status}`, summary: `${status === 'approved' ? 'Approved' : 'Rejected'} ${current.action_type}`, details: { actionId: input.actionId } });
  return mapAction(data as Record<string, unknown>);
}

export async function beginWorkspaceActionExecution(input: { userId: string; projectId: string; actionId: string }): Promise<WorkspaceAction> {
  const client = getSupabaseAdminClient(); const now = nowUnix();
  const { data, error } = await client.from('temuclaude_project_actions').update({ status: 'executing', updated_at: now }).eq('id', input.actionId).eq('project_id', input.projectId).eq('user_id', input.userId).eq('status', 'approved').gt('expires_at', now).select('*').maybeSingle();
  if (error) throw error;
  if (!data) throw new Error('Action is not approved or has expired.');
  await recordWorkspaceEvent({ userId: input.userId, projectId: input.projectId, eventType: 'action.executing', summary: `Executing ${data.action_type}`, details: { actionId: input.actionId } });
  return mapAction(data as Record<string, unknown>);
}

export async function finishWorkspaceAction(input: { userId: string; projectId: string; actionId: string; status: 'completed' | 'failed'; details?: Record<string, unknown> }): Promise<WorkspaceAction> {
  const now = nowUnix(); const client = getSupabaseAdminClient();
  const { data, error } = await client.from('temuclaude_project_actions').update({ status: input.status, updated_at: now, decision_payload: input.details || {} }).eq('id', input.actionId).eq('project_id', input.projectId).eq('user_id', input.userId).eq('status', 'executing').select('*').single();
  if (error) throw error;
  await recordWorkspaceEvent({ userId: input.userId, projectId: input.projectId, eventType: `action.${input.status}`, summary: `${input.status === 'completed' ? 'Completed' : 'Failed'} ${data.action_type}`, details: { actionId: input.actionId } });
  return mapAction(data as Record<string, unknown>);
}

export async function listWorkspaceProjects(userId: string): Promise<WorkspaceProject[]> {
  const { data, error } = await getSupabaseAdminClient()
    .from('temuclaude_projects')
    .select('*')
    .eq('user_id', userId)
    .eq('status', 'active')
    .order('updated_at', { ascending: false })
    .limit(100);

  if (error) throw error;
  return (data || []).map((row) => mapProject(row as Record<string, unknown>));
}

export async function createWorkspaceProject(input: {
  userId: string;
  title: string;
  profile: WorkspaceProfile;
}): Promise<WorkspaceProject> {
  const title = input.title.trim().replace(/\s+/g, ' ');
  if (!title || title.length > 120) throw new Error('Project title must be between 1 and 120 characters.');

  const createdAt = nowUnix();
  const project: WorkspaceProject = {
    id: newId('project'),
    user_id: input.userId,
    title,
    profile: input.profile,
    status: 'active',
    created_at: createdAt,
    updated_at: createdAt,
  };
  const client = getSupabaseAdminClient();
  const { data, error } = await client.from('temuclaude_projects').insert(project).select('*').single();
  if (error) throw error;

  await recordWorkspaceEvent({
    userId: input.userId,
    projectId: project.id,
    eventType: 'project.created',
    summary: 'Created project',
    details: { profile: input.profile },
  });
  return mapProject(data as Record<string, unknown>);
}

export async function getWorkspaceProject(userId: string, projectId: string): Promise<WorkspaceProject | null> {
  const { data, error } = await getSupabaseAdminClient()
    .from('temuclaude_projects')
    .select('*')
    .eq('id', projectId)
    .eq('user_id', userId)
    .eq('status', 'active')
    .maybeSingle();
  if (error) throw error;
  return data ? mapProject(data as Record<string, unknown>) : null;
}

export async function listWorkspaceFiles(userId: string, projectId: string): Promise<WorkspaceFile[]> {
  const project = await getWorkspaceProject(userId, projectId);
  if (!project) return [];
  const { data, error } = await getSupabaseAdminClient()
    .from('temuclaude_project_files')
    .select('*')
    .eq('project_id', projectId)
    .eq('user_id', userId)
    .order('file_path', { ascending: true });
  if (error) throw error;
  return (data || []).map((row) => mapFile(row as Record<string, unknown>));
}

export async function upsertWorkspaceFile(input: {
  userId: string;
  projectId: string;
  filePath: string;
  content: string;
  language?: string;
}): Promise<WorkspaceFile> {
  const project = await getWorkspaceProject(input.userId, input.projectId);
  if (!project) throw new Error('Project not found.');

  const filePath = input.filePath.trim();
  if (!filePath || filePath.length > 512 || filePath.startsWith('/') || filePath.includes('..')) {
    throw new Error('File path must be a relative path without traversal.');
  }
  const bytes = byteLength(input.content);
  if (bytes > MAX_FILE_BYTES) throw new Error('A workspace file cannot exceed 1 MB.');

  const client = getSupabaseAdminClient();
  const timestamp = nowUnix();
  const { data: existing, error: existingError } = await client
    .from('temuclaude_project_files')
    .select('id, created_at')
    .eq('project_id', input.projectId)
    .eq('file_path', filePath)
    .maybeSingle();
  if (existingError) throw existingError;

  const row = {
    id: existing?.id || newId('file'),
    project_id: input.projectId,
    user_id: input.userId,
    file_path: filePath,
    content: input.content,
    language: input.language?.trim() || null,
    content_sha256: sha256(input.content),
    byte_size: bytes,
    created_at: existing?.created_at || timestamp,
    updated_at: timestamp,
  };
  const { data, error } = await client
    .from('temuclaude_project_files')
    .upsert(row, { onConflict: 'project_id,file_path' })
    .select('*')
    .single();
  if (error) throw error;

  await client.from('temuclaude_projects').update({ updated_at: timestamp }).eq('id', input.projectId).eq('user_id', input.userId);
  await recordWorkspaceEvent({
    userId: input.userId,
    projectId: input.projectId,
    eventType: 'file.saved',
    summary: `Saved ${filePath}`,
    details: { bytes },
  });
  return mapFile(data as Record<string, unknown>);
}

export async function recordWorkspaceEvent(input: {
  userId: string;
  projectId: string;
  eventType: string;
  summary: string;
  details?: Record<string, unknown>;
}): Promise<void> {
  const { error } = await getSupabaseAdminClient().from('temuclaude_project_events').insert({
    id: newId('event'),
    project_id: input.projectId,
    user_id: input.userId,
    event_type: input.eventType,
    summary: input.summary,
    details: input.details || {},
    created_at: nowUnix(),
  });
  if (error) throw error;
}

export async function countWorkspaceEventsSince(input: {
  userId: string;
  projectId: string;
  eventType: string;
  sinceUnix: number;
}): Promise<number> {
  const project = await getWorkspaceProject(input.userId, input.projectId);
  if (!project) return 0;
  const { count, error } = await getSupabaseAdminClient()
    .from('temuclaude_project_events')
    .select('id', { count: 'exact', head: true })
    .eq('user_id', input.userId)
    .eq('project_id', input.projectId)
    .eq('event_type', input.eventType)
    .gte('created_at', input.sinceUnix);
  if (error) throw error;
  return count || 0;
}
