export type ModalChatResult = {
  ok: boolean;
  status: number;
  data: any;
  error?: string;
};

function modalBaseUrl(): string {
  return (process.env.TEMUCLAUDE_MODAL_URL || process.env.MODAL_API_URL || '').replace(/\/+$/, '');
}

export function isModalConfigured(): boolean {
  return Boolean(modalBaseUrl() && process.env.TEMUCLAUDE_MASTER_KEY);
}

export function isModalRequired(): boolean {
  return ['1', 'true', 'yes', 'on'].includes((process.env.TEMUCLAUDE_MODAL_REQUIRED || '').toLowerCase());
}

export async function callModalChatCompletions(body: any): Promise<ModalChatResult> {
  const baseUrl = modalBaseUrl();
  const masterKey = process.env.TEMUCLAUDE_MASTER_KEY || '';

  if (!baseUrl || !masterKey) {
    return {
      ok: false,
      status: 503,
      data: null,
      error: 'Modal is not configured. Set TEMUCLAUDE_MODAL_URL and TEMUCLAUDE_MASTER_KEY.',
    };
  }

  try {
    const response = await fetch(`${baseUrl}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${masterKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(115000),
    });

    const data = await response.json().catch(() => ({}));
    return {
      ok: response.ok,
      status: response.status,
      data,
      error: response.ok ? undefined : data?.error?.message || data?.error || response.statusText,
    };
  } catch (error) {
    return {
      ok: false,
      status: 503,
      data: null,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}
