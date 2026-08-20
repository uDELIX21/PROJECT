/** Thin API client: same-origin /api/v1 with CSRF double-submit (design §06). */

export const API = "/api/v1";

let csrfToken: string | null = null;

export class ApiClientError extends Error {
  code: string;
  status: number;
  details: unknown[];
  constructor(status: number, code: string, message: string, details: unknown[] = []) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function setCsrf(token: string | null) {
  csrfToken = token;
}

export async function api<T = any>(
  path: string,
  opts: { method?: string; body?: unknown; headers?: Record<string, string> } = {}
): Promise<T> {
  const method = opts.method ?? "GET";
  const headers: Record<string, string> = { ...(opts.headers ?? {}) };
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET" && method !== "HEAD") {
    if (!csrfToken) {
      const res = await fetch(`${API}/auth/csrf`, { credentials: "same-origin" });
      if (res.ok) csrfToken = (await res.json()).csrf_token;
    }
    if (csrfToken) headers["X-CSRF-Token"] = csrfToken;
  }
  const res = await fetch(`${API}${path}`, {
    method,
    headers,
    credentials: "same-origin",
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });
  if (res.status === 204) return undefined as T;
  let json: any = null;
  try {
    json = await res.json();
  } catch {
    /* non-JSON */
  }
  if (!res.ok) {
    const err = json?.error ?? {};
    throw new ApiClientError(
      res.status,
      err.code ?? "UNKNOWN",
      err.message ?? `Request failed (${res.status})`,
      err.details ?? []
    );
  }
  return json as T;
}

export interface MeResponse {
  user: { id: string; username: string; display_name?: string; status: string };
  roles: string[];
  permissions: string[];
  school: { id: string; name: string; motto?: string };
  active_year?: { id: string; name: string };
  active_term?: { id: string; name: string };
}

export function isAuthError(e: unknown): boolean {
  return e instanceof ApiClientError && e.status === 401;
}
