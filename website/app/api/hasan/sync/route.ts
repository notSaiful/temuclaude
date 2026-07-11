import { NextRequest, NextResponse } from 'next/server';
import { hasInternalAdminAccess } from '@/lib/internal-admin';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

// In-memory store for live state (Vercel serverless — persists within warm instances)
let liveState: any = null;
let lastSyncTime: number = 0;

export async function POST(req: NextRequest) {
  // A public caller must never be able to forge operational health or queue state.
  if (!hasInternalAdminAccess(req)) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 });
  }

  try {
    const data = await req.json();
    
    // Validate it looks like our sync data
    if (!data || !data.timestamp || !data.system) {
      return NextResponse.json({ error: 'Invalid sync data' }, { status: 400 });
    }

    // Store in memory
    liveState = data;
    lastSyncTime = Date.now();

    return NextResponse.json({
      success: true,
      message: 'Live state synced',
      daemons: data.daemons?.alive || 0,
      timestamp: data.timestamp,
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// GET — return the synced live state (used by the status API on Vercel)
export async function GET() {
  if (liveState) {
    const age = Math.floor((Date.now() - lastSyncTime) / 1000);
    return NextResponse.json({
      ...liveState,
      syncAge: age,
      dataSource: age < 30 ? 'sync-fresh' : 'sync-stale',
    });
  }

  return NextResponse.json({
    timestamp: new Date().toISOString(),
    system: 'hasan',
    status: 'deactivated',
    message: 'No sync data yet. Run the sync daemon on the local machine.',
    dataSource: 'none',
  });
}
