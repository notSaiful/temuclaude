import { NextRequest, NextResponse } from 'next/server';
import { verifyOtp } from '@/lib/otp-auth-server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try { const body = await req.json(); return NextResponse.json({ success: true, session: await verifyOtp({ ...body, purpose: 'signup' }) }); }
  catch (error) { return NextResponse.json({ error: error instanceof Error ? error.message : 'Could not verify code.' }, { status: 400 }); }
}
