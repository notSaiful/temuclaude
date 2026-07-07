import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export const runtime = 'nodejs';

const TEMUCLAUDE_DIR = process.env.TEMUCLAUDE_DIR || '/Users/saiful/temuclaude';

export async function GET() {
  try {
    const identityPath = path.join(TEMUCLAUDE_DIR, 'research', 'hasan_identity.py');
    const content = await fs.readFile(identityPath, 'utf-8');
    
    const purposeMatch = content.match(/"purpose":\s*"([^"]+)"/);
    const goalMatch = content.match(/"ultimate_goal":\s*"([^"]+)"/);
    const namedAfterMatch = content.match(/"named_after":\s*"([^"]+)"/);
    
    const missionCount = (content.match(/"priority"/g) || []).length;
    const neverDoCount = (content.match(/Never [A-Z]/g) || []).length;
    const principlesCount = (content.match(/"principle"/g) || []).length;
    
    return NextResponse.json({
      name: 'Hasan',
      named_after: namedAfterMatch?.[1] || 'Hasan ibn Ali (RA)',
      purpose: purposeMatch?.[1] || '',
      ultimate_goal: goalMatch?.[1] || '',
      integrity_verified: true,
      mission_count: missionCount,
      never_do_count: neverDoCount,
      principles_count: principlesCount,
      creator: 'Mohammad Saiful Haque (Ggs)',
    });
  } catch (error: any) {
    return NextResponse.json({ 
      name: 'Hasan',
      integrity_verified: false,
      error: error.message 
    }, { status: 500 });
  }
}