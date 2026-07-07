// Server-only client for the live Somba API. The merchant API key never leaves
// the server — the browser talks to our /api/somba/* proxy, which talks here.

const BASE = process.env.SOMBA_BASE_URL ?? "https://somba.ddns.net";
const KEY = process.env.SOMBA_API_KEY ?? "";

export function isLive(): boolean {
  return KEY.length > 0;
}

function idempotencyKey(): string {
  return `gf-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export class SombaError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

interface Opts {
  method?: string;
  body?: unknown;
  // extra idempotency safety for mutations
  idempotent?: boolean;
}

export async function somba<T = unknown>(
  path: string,
  opts: Opts = {},
): Promise<T> {
  const method = opts.method ?? "GET";
  const headers: Record<string, string> = {
    Authorization: `Bearer ${KEY}`,
  };
  const mutating = method !== "GET" && method !== "HEAD";
  if (mutating) {
    headers["Content-Type"] = "application/json";
    headers["Idempotency-Key"] = idempotencyKey();
  }

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    cache: "no-store",
  });

  const text = await res.text();
  let json: unknown = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    /* non-JSON response */
  }

  if (!res.ok) {
    const err = (json as { error?: { code?: string; message?: string } })
      ?.error;
    throw new SombaError(
      res.status,
      err?.code ?? "request_failed",
      err?.message ?? `Somba API error (${res.status})`,
    );
  }
  return json as T;
}
