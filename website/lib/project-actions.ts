import crypto from 'crypto';
import { getSupabaseAdminClient } from '@/lib/supabase-server';
import { getWorkspaceProject, recordWorkspaceEvent } from '@/lib/workspace';

export type ProjectActionType = 'agent.run' | 'package.install' | 'network.enable' | 'github.connect' | 'deploy.preview' | 'deploy.production';
export type ProjectActionStatus = 'requested' | 'approved' | 'rejected' | 'executing' | 'completed' | 'failed' | 'cancelled';

export type ProjectAction = {
  id: string;
  project_id: string;
  user_id: string;
  action_type: ProjectActionType;
  status: ProjectActionStatus;
  requested_payload: Record<string, unknown>;
  decision_payload: Record<string, unknown>;
  requested_at: number;
  decided_at: number | null;
  expires_at: number;
  created_at: number;
  updated_at: number;
};

const APPROVAL_REQUIRED = new Set<ProjectActionType>(['agent.run', 'package.install', 'network.enable', 'github.connect', 'deploy.preview', 'deploy.production']);
const ACTION_TTLS: Record<ProjectActionType, number> = {
  'agent.run': 60 * 60,
  'package.install': 30 * 60,
  'network.enable': 15 * 60,
  'github.connect': 60 * 60,
  'deploy.preview': 30 * 60,
  'deploy.production': 10 * 60,
};
const ALLOWED_TYPES: ProjectActionType[] = ['agent.run', 'package.install', 'network.enable', 'github.connect', 'deploy.preview', 'deploy.production'];

function nowUnix() {
  return Math.floor(Date.now() / 1000);
}

function newId(prefix: string) {
  return `${prefix}_${crypto.randomBytes(16).toString('hex')}`;
}

function mapAction(row: Record<string, unknown>): ProjectAction {
  return {
    id: String(row.id),
    project_id: String(row.project_id),
    user_id: String(row.user_id),
    action_type: row.action_type as ProjectActionType,
    status: row.status as ProjectActionStatus,
    requested_payload: (row.requested_payload && typeof row.requested_payload === 'object' ? row.requested_payload : {}) as Record<string, unknown>,
    decision_payload: (row.decision_payload && typeof row.decision_payload === 'object' ? row.decision_payload : {}) as Record<string, unknown>,
    requested_at: Number(row.requested_at),
    decided_at: row.decided_at == null ? null : Number(row.decided_at),
    expires_at: Number(row.expires_at),
    created_at: Number(row.created_at),
    updated_at: Number(row.updated_at),
  };
}

function sanitizePayload(payload: unknown): Record<string, unknown> {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return {};
  const json = JSON.stringify(payload);
  if (Buffer.byteLength(json, 'utf8') > 16_384) throw new Error('Action payload cannot exceed 16 KB.');
  return JSON.parse(json) as Record<string, unknown>;
}

export function isProjectActionType(value: unknown): value is ProjectActionType {
  return typeof value === 'string' && (ALLOWED_TYPES as string[]).includes(value);
}

export async function listProjectActions(userId: string, projectId: string): Promise<ProjectAction[]> {
  const project = await getWorkspaceProject(userId, projectId);
  if (!project) return [];
  const { data, error } = await getSupabaseAdminClient()
    .from('temuclaude_project_actions')
    .select('*')
    .eq('project_id', projectId)
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(50);
  if (error) throw error;
  return (data || []).map((row) => mapAction(row as Record<string, unknown>));
}

export async function requestProjectAction(input: {
  userId: string;
  projectId: string;
  actionType: ProjectActionType;
  payload?: unknown;
}): Promise<ProjectAction> {
  const project = await getWorkspaceProject(input.userId, input.projectId);
  if (!project) throw new Error('Project not found.');
  if (!APPROVAL_REQUIRED.has(input.actionType)) throw new Error('Unsupported project action.');
  const timestamp = nowUnix();
  const row = {
    id: newId('action'),
    project_id: input.projectId,
    user_id: input.userId,
    action_type: input.actionType,
    status: 'requested' as ProjectActionStatus,
    requested_payload: sanitizePayload(input.payload),
    decision_payload: {},
    requested_at: timestamp,
    expires_at: timestamp + ACTION_TTLS[input.actionType],
    created_at: timestamp,
    updated_at: timestamp,
  };
  const { data, error } = await getSupabaseAdminClient().from('temuclaude_project_actions').insert(row).select('*').single();
  if (error) throw error;
  await recordWorkspaceEvent({
    userId: input.userId,
    projectId: input.projectId,
    eventType: 'project.action.requested',
    summary: `Requested approval for ${input.actionType}`,
    details: { actionId: row.id, actionType: input.actionType },
  }).catch(() => undefined);
  return mapAction(data as Record<string, unknown>);
}

export async function decideProjectAction(input: {
  userId: string;
  projectId: string;
  actionId: string;
  decision: 'approved' | 'rejected' | 'cancelled';
  payload?: unknown;
}): Promise<ProjectAction> {
  const project = await getWorkspaceProject(input.userId, input.projectId);
  if (!project) throw new Error('Project not found.');
  const timestamp = nowUnix();
  const { data: existing, error: readError } = await getSupabaseAdminClient()
    .from('temuclaude_project_actions')
    .select('*')
    .eq('id', input.actionId)
    .eq('project_id', input.projectId)
    .eq('user_id', input.userId)
    .maybeSingle();
  if (readError) throw readError;
  if (!existing) throw new Error('Action not found.');
  const action = mapAction(existing as Record<string, unknown>);
  if (action.status !== 'requested') throw new Error('Only requested actions can be decided.');
  if (action.expires_at <= timestamp) throw new Error('Action approval expired. Request it again.');

  const { data, error } = await getSupabaseAdminClient()
    .from('temuclaude_project_actions')
    .update({
      status: input.decision,
      decision_payload: sanitizePayload(input.payload),
      decided_at: timestamp,
      updated_at: timestamp,
    })
    .eq('id', input.actionId)
    .eq('project_id', input.projectId)
    .eq('user_id', input.userId)
    .select('*')
    .single();
  if (error) throw error;
  await recordWorkspaceEvent({
    userId: input.userId,
    projectId: input.projectId,
    eventType: `project.action.${input.decision}`,
    summary: `${input.decision} ${action.action_type}`,
    details: { actionId: input.actionId, actionType: action.action_type },
  }).catch(() => undefined);
  return mapAction(data as Record<string, unknown>);
}

export async function executeApprovedProjectAction(input: { userId: string; projectId: string; actionId: string }): Promise<ProjectAction> {
  const actions = await listProjectActions(input.userId, input.projectId);
  const action = actions.find((item) => item.id === input.actionId);
  if (!action) throw new Error('Action not found.');
  if (action.status !== 'approved') throw new Error('Action must be approved before execution.');
  const timestamp = nowUnix();
  if (action.expires_at <= timestamp) throw new Error('Approved action expired. Request approval again.');

  const client = getSupabaseAdminClient();
  await client.from('temuclaude_project_actions').update({ status: 'executing', updated_at: timestamp }).eq('id', action.id);
  const completion = nowUnix();
  const { data, error } = await client
    .from('temuclaude_project_actions')
    .update({
      status: 'completed',
      updated_at: completion,
      decision_payload: {
        ...action.decision_payload,
        execution: executionSummary(action),
        executedAt: completion,
      },
    })
    .eq('id', action.id)
    .select('*')
    .single();
  if (error) throw error;
  await recordWorkspaceEvent({
    userId: input.userId,
    projectId: input.projectId,
    eventType: 'project.action.completed',
    summary: `Completed ${action.action_type}`,
    details: { actionId: action.id, actionType: action.action_type },
  }).catch(() => undefined);
  return mapAction(data as Record<string, unknown>);
}

function executionSummary(action: ProjectAction) {
  switch (action.action_type) {
    case 'github.connect':
      return 'GitHub App installation authorization recorded; repository access must use the installation token broker.';
    case 'deploy.production':
      return 'Production promotion approved and queued for Vercel integration handoff.';
    case 'deploy.preview':
      return 'Preview deployment approved and queued for isolated build execution.';
    case 'package.install':
      return 'Package installation approved for the isolated execution environment.';
    case 'agent.run':
      return 'Agent action approved and queued with the requested constraints.';
    case 'network.enable':
      return 'Network egress window approved for the isolated execution environment.';
  }
}
