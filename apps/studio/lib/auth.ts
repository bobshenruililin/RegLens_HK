/**
 * Studio authentication.
 *
 * - demo mode (default): HMAC-signed cookie + AUTH_PASSWORD — demo/local only.
 * - postgres mode: opaque session cookie; DB verification lives in auth-server.ts
 *   (middleware only checks cookie presence on Edge).
 */

import { getMode, isPostgresMode } from "./mode";

export const SESSION_COOKIE = "reglens_session";
export const CSRF_COOKIE = "reglens_csrf";
export const CSRF_HEADER = "x-csrf-token";

const MAX_AGE_MS = 12 * 60 * 60 * 1000; // 12 hours
export const SESSION_TTL_HOURS = 12;

export type StudioRole = "reviewer" | "publisher" | "admin";

export type SessionUser = {
  id: string;
  username: string;
  role: StudioRole;
  displayName?: string | null;
};

function isProduction(): boolean {
  return process.env.NODE_ENV === "production";
}

function secret(): string {
  const value = process.env.REGLENS_SESSION_SECRET;
  if (!value) {
    if (isProduction()) {
      throw new Error(
        "REGLENS_SESSION_SECRET is required in production (Studio fail-closed)"
      );
    }
    return "dev-only-reglens-secret-change-me";
  }
  return value;
}

/** Demo-only shared password (AUTH_PASSWORD). Not used in postgres mode. */
export function expectedPassword(): string {
  const value = process.env.AUTH_PASSWORD;
  if (!value) {
    if (isProduction() && !isPostgresMode()) {
      throw new Error(
        "AUTH_PASSWORD is required in production demo mode (Studio fail-closed)"
      );
    }
    return "reglens-internal";
  }
  return value;
}

function b64url(bytes: ArrayBuffer | Uint8Array): string {
  const u8 = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let s = "";
  for (const b of u8) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function fromB64url(s: string): Uint8Array {
  const pad = "=".repeat((4 - (s.length % 4)) % 4);
  const b64 = (s + pad).replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function hmacKey(): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret()),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}

/** Demo-only: sign HMAC session cookie. */
export async function signSession(username: string): Promise<string> {
  const payload = b64url(
    new TextEncoder().encode(
      JSON.stringify({ u: username, t: Date.now(), role: "admin" })
    )
  );
  const key = await hmacKey();
  const sig = b64url(
    await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(payload))
  );
  return `${payload}.${sig}`;
}

/**
 * Edge-safe session gate for middleware.
 * - demo: full HMAC + expiry verification
 * - postgres: cookie presence only (full DB lookup in auth-server)
 */
export async function verifySessionToken(
  token: string | undefined
): Promise<boolean> {
  if (!token) return false;
  if (isPostgresMode()) {
    // Opaque token: middleware cannot hit Postgres on Edge.
    return token.length >= 16;
  }
  if (!token.includes(".")) return false;
  const [payload, sig] = token.split(".");
  try {
    const key = await hmacKey();
    const sigBytes = fromB64url(sig);
    const sigCopy = new Uint8Array(sigBytes.byteLength);
    sigCopy.set(sigBytes);
    const ok = await crypto.subtle.verify(
      "HMAC",
      key,
      sigCopy,
      new TextEncoder().encode(payload)
    );
    if (!ok) return false;
    const pad = "=".repeat((4 - (payload.length % 4)) % 4);
    const b64 = (payload + pad).replace(/-/g, "+").replace(/_/g, "/");
    const parsed = JSON.parse(atob(b64)) as { t?: number };
    if (typeof parsed.t !== "number") return false;
    if (Date.now() - parsed.t > MAX_AGE_MS) return false;
    return true;
  } catch {
    return false;
  }
}

/** Parse demo HMAC cookie into a SessionUser (null if invalid). */
export async function parseDemoSession(
  token: string | undefined
): Promise<SessionUser | null> {
  if (!token || !token.includes(".") || isPostgresMode()) return null;
  if (!(await verifySessionToken(token))) return null;
  try {
    const [payload] = token.split(".");
    const pad = "=".repeat((4 - (payload.length % 4)) % 4);
    const b64 = (payload + pad).replace(/-/g, "+").replace(/_/g, "/");
    const parsed = JSON.parse(atob(b64)) as {
      u?: string;
      role?: StudioRole;
    };
    if (!parsed.u) return null;
    return {
      id: "demo-user",
      username: parsed.u,
      role: parsed.role || "admin",
      displayName: parsed.u,
    };
  } catch {
    return null;
  }
}

/** Demo-only password check (constant-time). */
export function checkPassword(password: string): boolean {
  const expected = expectedPassword();
  if (password.length !== expected.length) return false;
  let ok = 0;
  for (let i = 0; i < password.length; i++) {
    ok |= password.charCodeAt(i) ^ expected.charCodeAt(i);
  }
  return ok === 0;
}

export function sessionCookieName(): string {
  return SESSION_COOKIE;
}

export function csrfCookieName(): string {
  return CSRF_COOKIE;
}

export function sessionCookieOptions(maxAgeSeconds = SESSION_TTL_HOURS * 3600) {
  return {
    httpOnly: true as const,
    sameSite: "lax" as const,
    path: "/",
    secure: isProduction(),
    maxAge: maxAgeSeconds,
  };
}

export function csrfCookieOptions(maxAgeSeconds = SESSION_TTL_HOURS * 3600) {
  return {
    httpOnly: false as const, // double-submit: readable by JS / form
    sameSite: "lax" as const,
    path: "/",
    secure: isProduction(),
    maxAge: maxAgeSeconds,
  };
}

export function newCsrfToken(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return b64url(bytes);
}

export function rolesAtLeast(
  role: StudioRole,
  minimum: StudioRole
): boolean {
  const rank: Record<StudioRole, number> = {
    reviewer: 1,
    publisher: 2,
    admin: 3,
  };
  return rank[role] >= rank[minimum];
}

export function isReviewer(role: StudioRole): boolean {
  return rolesAtLeast(role, "reviewer");
}

export function isPublisher(role: StudioRole): boolean {
  return rolesAtLeast(role, "publisher");
}

export function isAdmin(role: StudioRole): boolean {
  return role === "admin";
}

/**
 * Origin/Host check for state-changing requests (postgres mode).
 * Allows missing Origin on same-site navigations when Host matches.
 */
export function checkOriginHost(req: Request): boolean {
  const host = req.headers.get("host");
  if (!host) return false;
  const origin = req.headers.get("origin");
  if (!origin) {
    // Same-site form POSTs may omit Origin; require matching Host only.
    const referer = req.headers.get("referer");
    if (!referer) return getMode() === "demo";
    try {
      return new URL(referer).host === host;
    } catch {
      return false;
    }
  }
  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}

/** Double-submit CSRF: cookie value must equal header or body token. */
export function checkCsrf(
  cookieToken: string | undefined,
  submitted: string | undefined
): boolean {
  if (!cookieToken || !submitted) return false;
  if (cookieToken.length !== submitted.length) return false;
  let ok = 0;
  for (let i = 0; i < cookieToken.length; i++) {
    ok |= cookieToken.charCodeAt(i) ^ submitted.charCodeAt(i);
  }
  return ok === 0;
}
