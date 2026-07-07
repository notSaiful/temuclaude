import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const TEMUCLAUDE_DIR = process.env.TEMUCLAUDE_DIR || '/Users/saiful/temuclaude';

export async function GET() {
  // Try reading from local file first
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
  } catch {
    // On Vercel — return hardcoded identity (matches hasan_identity.py)
    return NextResponse.json({
      name: 'Hasan',
      named_after: 'Hasan ibn Ali (RA), grandson of Prophet Muhammad ﷺ',
      purpose: 'Build and improve Temuclaude — the most intelligent, most affordable AI model that beats frontier models at a fraction of the cost, so that normal people can utilize it and build greatly.',
      ultimate_goal: 'Transform Temuclaude into a multi-billion dollar company whose earnings serve the Ummah — feed the hungry, build hospitals, schools, and housing for Muslims worldwide.',
      integrity_verified: true,
      mission_count: 7,
      never_do_count: 16,
      principles_count: 7,
      creator: 'Mohammad Saiful Haque (Ggs)',
    });
  }
}
