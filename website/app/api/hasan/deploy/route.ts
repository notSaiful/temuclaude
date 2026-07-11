import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import { hasInternalAdminAccess } from '@/lib/internal-admin';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const TEMUCLAUDE_DIR = process.env.TEMUCLAUDE_DIR || '/Users/saiful/temuclaude';
const DEPLOY_FILE = path.join(TEMUCLAUDE_DIR, 'research', 'deployment', 'deployment_queue.json');

async function readDeploy(): Promise<any> {
  try {
    const data = await fs.readFile(DEPLOY_FILE, 'utf-8');
    return JSON.parse(data);
  } catch {
    return null;
  }
}

async function writeDeploy(data: any): Promise<void> {
  await fs.writeFile(DEPLOY_FILE, JSON.stringify(data, null, 2));
}

// GET — return deployment queue status (pending findings, agent scaling, last approval)
export async function GET(req: NextRequest) {
  if (!hasInternalAdminAccess(req)) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  try {
    const data = await readDeploy();
    if (!data) {
      return NextResponse.json({
        pending_findings: [],
        agent_scaling: { current_research_agents: 3, min: 1, max: 8 },
        last_permission_request: null,
        next_permission_eligible: null,
      });
    }

    const pendingCount = (data.pending_findings || []).filter((f: any) => f.status === 'pending_approval').length;
    const stagingCount = (data.pending_findings || []).filter((f: any) => f.status === 'in_staging').length;

    return NextResponse.json({
      pending_findings: data.pending_findings || [],
      pending_count: pendingCount,
      staging_count: stagingCount,
      approved_count: (data.approved_deployments || []).length,
      rejected_count: (data.rejected_deployments || []).length,
      last_permission_request: data.last_permission_request,
      next_permission_eligible: data.next_permission_eligible,
      agent_scaling: data.agent_scaling || { current_research_agents: 3, min: 1, max: 8 },
      rules: data.rules,
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// POST — approve/reject findings, or scale agents
export async function POST(req: NextRequest) {
  if (!hasInternalAdminAccess(req)) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  try {
    const body = await req.json();
    const { action } = body;

    const data = await readDeploy();
    if (!data) {
      return NextResponse.json({ error: 'Deployment queue not found' }, { status: 404 });
    }

    // APPROVE a finding
    if (action === 'approve') {
      const { finding_id } = body;
      const finding = (data.pending_findings || []).find((f: any) => f.id === finding_id);
      if (!finding) {
        return NextResponse.json({ error: 'Finding not found' }, { status: 404 });
      }
      finding.status = 'approved';
      finding.approved_at = new Date().toISOString();
      finding.approved_by = 'Ggs';
      data.approved_deployments = data.approved_deployments || [];
      data.approved_deployments.push(finding);
      data.pending_findings = (data.pending_findings || []).filter((f: any) => f.id !== finding_id);
      await writeDeploy(data);
      return NextResponse.json({ success: true, message: `Finding "${finding.title}" approved for deployment` });
    }

    // REJECT a finding
    if (action === 'reject') {
      const { finding_id, reason } = body;
      const finding = (data.pending_findings || []).find((f: any) => f.id === finding_id);
      if (!finding) {
        return NextResponse.json({ error: 'Finding not found' }, { status: 404 });
      }
      finding.status = 'rejected';
      finding.rejected_at = new Date().toISOString();
      finding.rejected_by = 'Ggs';
      finding.rejection_reason = reason || 'No reason provided';
      data.rejected_deployments = data.rejected_deployments || [];
      data.rejected_deployments.push(finding);
      data.pending_findings = (data.pending_findings || []).filter((f: any) => f.id !== finding_id);
      await writeDeploy(data);
      return NextResponse.json({ success: true, message: `Finding "${finding.title}" rejected` });
    }

    // APPROVE ALL pending
    if (action === 'approve_all') {
      const pending = (data.pending_findings || []).filter((f: any) => f.status === 'pending_approval');
      const now = new Date().toISOString();
      for (const f of pending) {
        f.status = 'approved';
        f.approved_at = now;
        f.approved_by = 'Ggs';
      }
      data.approved_deployments = data.approved_deployments || [];
      data.approved_deployments.push(...pending);
      data.pending_findings = (data.pending_findings || []).filter((f: any) => f.status !== 'approved');
      await writeDeploy(data);
      return NextResponse.json({ success: true, message: `${pending.length} findings approved` });
    }

    // SCALE AGENTS — add or remove research agents
    if (action === 'scale_agents') {
      const { new_count, reason } = body;
      const count = parseInt(new_count);
      if (isNaN(count) || count < 1 || count > 8) {
        return NextResponse.json({ error: 'Agent count must be 1-8' }, { status: 400 });
      }
      const old = data.agent_scaling?.current_research_agents || 3;
      data.agent_scaling = data.agent_scaling || {};
      data.agent_scaling.current_research_agents = count;
      data.agent_scaling.last_scaled = new Date().toISOString();
      data.agent_scaling.scale_reason = reason || 'Manual adjustment';
      data.agent_scaling.history = data.agent_scaling.history || [];
      data.agent_scaling.history.push({
        timestamp: new Date().toISOString(),
        from: old,
        to: count,
        reason: reason || 'Manual adjustment',
      });
      await writeDeploy(data);
      return NextResponse.json({ success: true, message: `Research agents scaled from ${old} to ${count}`, old, new: count });
    }

    // REQUEST PERMISSION (Hasan marks findings as pending_approval)
    if (action === 'request_permission') {
      const { findings } = body;
      const now = new Date().toISOString();
      const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();

      // Mark in-staging findings as pending_approval
      for (const f of (data.pending_findings || [])) {
        if (f.status === 'in_staging') {
          f.status = 'pending_approval';
          f.requested_at = now;
        }
      }

      // Add any new findings passed in
      if (findings && Array.isArray(findings)) {
        for (const f of findings) {
          data.pending_findings = data.pending_findings || [];
          data.pending_findings.push({
            ...f,
            id: f.id || `finding_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            status: 'pending_approval',
            requested_at: now,
          });
        }
      }

      data.last_permission_request = now;
      data.next_permission_eligible = nextWeek;
      await writeDeploy(data);

      const pendingCount = (data.pending_findings || []).filter((f: any) => f.status === 'pending_approval').length;
      return NextResponse.json({
        success: true,
        message: `Permission requested. ${pendingCount} findings pending Ggs's approval.`,
        pending_count: pendingCount,
        next_permission_eligible: nextWeek,
      });
    }

    return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
