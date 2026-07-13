import { NextRequest, NextResponse } from 'next/server';
import { startOtp } from '@/lib/otp-auth-server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try { const body = await req.json(); return NextResponse.json({ success: true, ...(await startOtp({ email: body.email, name: body.name, purpose: 'signup' })) }); }
  catch (error) { return NextResponse.json({ error: error instanceof Error ? error.message : 'Could not send verification code.' }, { status: 400 }); }
}
