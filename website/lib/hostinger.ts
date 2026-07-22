const HOSTINGER_API_BASE = 'https://developers.hostinger.com';

function getHostingerToken() {
  return process.env.HOSTINGER_API_TOKEN || '';
}

export function isHostingerApiConfigured() {
  return Boolean(getHostingerToken());
}

export async function hostingerRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getHostingerToken();
  if (!token) {
    throw new Error('HOSTINGER_API_TOKEN is not configured.');
  }

  const response = await fetch(`${HOSTINGER_API_BASE}${path}`, {
    ...init,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...(init.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof data?.error === 'string' ? data.error : `Hostinger API error: ${response.status}`;
    throw new Error(message);
  }

  return data as T;
}

export async function getHostingerEmailDnsStatus(profileUuid: string) {
  return hostingerRequest(`/api/reach/v1/profiles/${profileUuid}/domains/dns-status`);
}
