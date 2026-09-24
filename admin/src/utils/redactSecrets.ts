/**
 * Secret Redaction Utility for MAX System Console
 * Redacts sensitive fields (passwords, tokens, API keys, credentials)
 * before rendering in audit tables, logs, traces, or configuration displays.
 */

const SECRET_PATTERNS = [
  /password/i,
  /token/i,
  /secret/i,
  /api[_-]?key/i,
  /authorization/i,
  /cookie/i,
  /credential/i,
  /private[_-]?key/i,
  /bearer/i,
  /pwd/i,
];

export function redactValue(key: string, value: unknown): unknown {
  if (value === null || value === undefined) return value;

  const isSecretKey = SECRET_PATTERNS.some((pattern) => pattern.test(key));
  if (isSecretKey) {
    return '[REDACTED_SECRET]';
  }

  if (typeof value === 'string') {
    // Check if string looks like JWT or API Key token
    if (value.startsWith('eyJ') || value.startsWith('sk-') || value.startsWith('ghp_')) {
      return '[REDACTED_TOKEN]';
    }
  }

  if (typeof value === 'object' && !Array.isArray(value)) {
    const redactedObj: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      redactedObj[k] = redactValue(k, v);
    }
    return redactedObj;
  }

  return value;
}

export function redactJson(data: Record<string, unknown>): Record<string, unknown> {
  return redactValue('root', data) as Record<string, unknown>;
}
