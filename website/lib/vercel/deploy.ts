type DeploymentRequest = { name: string; gitSource?: { type: 'github'; repoId: string; ref: string }; target?: 'production' };
type DeploymentResult = { id: string; url: string; state: string };

function credentials() {
  const token = process.env.VERCEL_TOKEN?.trim();
  const teamId = process.env.VERCEL_TEAM_ID?.trim();
  if (!token) throw new Error('Vercel deployment is not configured.');
  return { token, teamId };
}

export async function createVercelDeployment(input: DeploymentRequest): Promise<DeploymentResult> {
  const { token, teamId } = credentials();
  const endpoint = new URL('https://api.vercel.com/v13/deployments');
  if (teamId) endpoint.searchParams.set('teamId', teamId);
  const response = await fetch(endpoint, { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify(input), cache: 'no-store' });
  const data = await response.json().catch(() => ({})) as Record<string, unknown>;
  if (!response.ok) throw new Error(`Vercel deployment failed (${response.status}).`);
  if (typeof data.id !== 'string' || typeof data.url !== 'string') throw new Error('Vercel returned an invalid deployment response.');
  return { id: data.id, url: `https://${data.url}`, state: typeof data.readyState === 'string' ? data.readyState : 'QUEUED' };
}
