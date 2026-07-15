const DEFAULT_CHAT_ENDPOINT = '/api/chat';

/**
 * Accept either the full chat endpoint or a Cloud Run service base URL.
 *
 * Vercel environment variables are easy to configure with the URL printed by
 * `gcloud run deploy`, which points at `/`. The Playground must target the
 * route itself; otherwise the browser's CORS preflight receives a 405 before
 * the request reaches the model workflow.
 */
export function resolveChatEndpoint(configuredUrl: string | undefined): string {
  const value = configuredUrl?.trim();
  if (!value || value === '/') return DEFAULT_CHAT_ENDPOINT;
  if (value === `${DEFAULT_CHAT_ENDPOINT}/`) return DEFAULT_CHAT_ENDPOINT;

  try {
    const url = new URL(value);
    if (url.pathname === '/' || url.pathname === '') {
      url.pathname = DEFAULT_CHAT_ENDPOINT;
    } else if (url.pathname === `${DEFAULT_CHAT_ENDPOINT}/`) {
      url.pathname = DEFAULT_CHAT_ENDPOINT;
    }
    return url.toString();
  } catch {
    // Preserve non-URL values rather than guessing at custom proxy paths.
    return value;
  }
}
