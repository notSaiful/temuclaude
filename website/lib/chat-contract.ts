export const CHAT_LIMITS = {
  maxMessages: 50,
  maxCharactersPerMessage: 20_000,
  maxTotalCharacters: 100_000,
  maxOutputTokens: 32_768,
} as const;

export type ValidatedMessage<Role extends string> = {
  role: Role;
  content: string;
};

export type ValidationResult<Role extends string> =
  | { messages: ValidatedMessage<Role>[] }
  | { error: string };

export function validateChatMessages<Role extends string>(
  value: unknown,
  allowedRoles: readonly Role[],
): ValidationResult<Role> {
  if (!Array.isArray(value) || value.length === 0) {
    return { error: 'messages must be a non-empty array' };
  }
  if (value.length > CHAT_LIMITS.maxMessages) {
    return { error: `messages cannot contain more than ${CHAT_LIMITS.maxMessages} entries` };
  }

  const roles = new Set<string>(allowedRoles);
  const messages: ValidatedMessage<Role>[] = [];
  let totalCharacters = 0;
  let hasUserMessage = false;

  for (const candidate of value) {
    if (!candidate || typeof candidate !== 'object') {
      return { error: 'each message must be an object' };
    }
    const { role, content } = candidate as Record<string, unknown>;
    if (typeof role !== 'string' || !roles.has(role) || typeof content !== 'string' || !content.trim()) {
      return { error: `each message requires one of these roles (${allowedRoles.join(', ')}) and non-empty content` };
    }
    if (content.length > CHAT_LIMITS.maxCharactersPerMessage) {
      return { error: `each message must be ${CHAT_LIMITS.maxCharactersPerMessage.toLocaleString()} characters or fewer` };
    }
    totalCharacters += content.length;
    if (totalCharacters > CHAT_LIMITS.maxTotalCharacters) {
      return { error: `messages must be ${CHAT_LIMITS.maxTotalCharacters.toLocaleString()} characters or fewer in total` };
    }
    hasUserMessage ||= role === 'user';
    messages.push({ role: role as Role, content });
  }

  return hasUserMessage ? { messages } : { error: 'messages must include at least one user message' };
}

export function validateTemperature(value: unknown): number | undefined | { error: string } {
  if (value === undefined) return undefined;
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 2) {
    return { error: 'temperature must be a number from 0 to 2' };
  }
  return value;
}

export function validateMaxTokens(value: unknown): number | undefined | { error: string } {
  if (value === undefined) return undefined;
  if (!Number.isInteger(value) || (value as number) < 1 || (value as number) > CHAT_LIMITS.maxOutputTokens) {
    return { error: `max_tokens must be an integer from 1 to ${CHAT_LIMITS.maxOutputTokens}` };
  }
  return value as number;
}
