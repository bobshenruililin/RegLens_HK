/**
 * Node-only auth helpers (Postgres sessions, login/logout).
 * Do not import from Edge middleware — uses `pg` and Node crypto.
 */

import { createHash, randomBytes } from "node:crypto";
import { cookies } from "next/headers";
import {
  CSRF_COOKIE,
  CSRF_HEADER,
  SESSION_COOKIE,
  SESSION_TTL_HOURS,
  checkCsrf,
  checkOriginHost,
  checkPassword,
  csrfCookieOptions,
  isAdmin,
  isPublisher,
  isReviewer,
  newCsrfToken,
  parseDemoSession,
  sessionCookieOptions,
  signSession,
  type SessionUser,
  type StudioRole,
} from "./auth";
import { query, withTransaction } from "./db";
import { isDemoMode, isPostgresMode } from "./mode";
import { verifyPassword } from "./password";

export function hashSessionToken(token: string): string {
  return createHash("sha256").update(token, "utf8").digest("hex");
}

export function newOpaqueToken(): string {
  return randomBytes(32).toString("base64url");
}

export async function lookupPostgresSession(
  token: string
): Promise<SessionUser | null> {
  const digest = hashSessionToken(token);
  const { rows } = await query<{
    user_id: string;
    username: string;
    role: StudioRole;
    display_name: string | null;
    user_active: boolean;
  }>(
    `
    SELECT
      s.user_id,
      u.username,
      u.role,
      u.display_name,
      u.active AS user_active
    FROM sessions s
    JOIN users u ON u.id = s.user_id
    WHERE s.token_hash = $1
      AND s.revoked_at IS NULL
      AND s.expires_at > now()
      AND u.active = TRUE
    `,
    [digest]
  );
  const row = rows[0];
  if (!row || !row.user_active) return null;
  await query(`UPDATE sessions SET last_seen_at = now() WHERE token_hash = $1`, [
    digest,
  ]);
  return {
    id: row.user_id,
    username: row.username,
    role: row.role,
    displayName: row.display_name,
  };
}

export async function createPostgresSession(
  userId: string,
  meta?: { userAgent?: string | null; ipAddress?: string | null }
): Promise<string> {
  const token = newOpaqueToken();
  const digest = hashSessionToken(token);
  await query(
    `
    INSERT INTO sessions (user_id, token_hash, expires_at, user_agent, ip_address, last_seen_at)
    VALUES ($1, $2, now() + make_interval(hours => $3::int), $4, $5, now())
    `,
    [
      userId,
      digest,
      SESSION_TTL_HOURS,
      meta?.userAgent ?? null,
      meta?.ipAddress ?? null,
    ]
  );
  return token;
}

export async function revokePostgresSession(token: string): Promise<void> {
  const digest = hashSessionToken(token);
  await query(
    `
    UPDATE sessions
    SET revoked_at = now()
    WHERE token_hash = $1 AND revoked_at IS NULL
    `,
    [digest]
  );
}

export async function verifyUserCredentials(
  username: string,
  password: string
): Promise<SessionUser | null> {
  const { rows } = await query<{
    id: string;
    username: string;
    password_hash: string;
    role: StudioRole;
    active: boolean;
    display_name: string | null;
  }>(
    `
    SELECT id, username, password_hash, role, active, display_name
    FROM users
    WHERE username = $1
    `,
    [username.trim()]
  );
  const row = rows[0];
  if (!row || !row.active) return null;
  if (!verifyPassword(password, row.password_hash)) return null;
  return {
    id: row.id,
    username: row.username,
    role: row.role,
    displayName: row.display_name,
  };
}

export async function getCurrentUser(): Promise<SessionUser | null> {
  const jar = cookies();
  const token = jar.get(SESSION_COOKIE)?.value;
  if (!token) return null;
  if (isDemoMode()) {
    return parseDemoSession(token);
  }
  return lookupPostgresSession(token);
}

export async function requireUser(): Promise<SessionUser> {
  const user = await getCurrentUser();
  if (!user) {
    throw new AuthRequiredError();
  }
  return user;
}

export async function requireRole(minimum: StudioRole): Promise<SessionUser> {
  const user = await requireUser();
  if (minimum === "admin" && !isAdmin(user.role)) {
    throw new ForbiddenError("admin required");
  }
  if (minimum === "publisher" && !isPublisher(user.role)) {
    throw new ForbiddenError("publisher required");
  }
  if (minimum === "reviewer" && !isReviewer(user.role)) {
    throw new ForbiddenError("reviewer required");
  }
  return user;
}

export class AuthRequiredError extends Error {
  status = 401;
  constructor() {
    super("unauthorized");
    this.name = "AuthRequiredError";
  }
}

export class ForbiddenError extends Error {
  status = 403;
  constructor(message = "forbidden") {
    super(message);
    this.name = "ForbiddenError";
  }
}

export class CsrfError extends Error {
  status = 403;
  constructor(message = "csrf failed") {
    super(message);
    this.name = "CsrfError";
  }
}

/**
 * Enforce Origin/Host + CSRF for postgres POST mutations.
 * Demo mode skips CSRF (keeps make verify / local HMAC flow simple).
 */
export async function assertMutationSafe(
  req: Request,
  bodyCsrf?: string | null
): Promise<void> {
  if (isDemoMode()) return;
  if (!checkOriginHost(req)) {
    throw new CsrfError("origin/host check failed");
  }
  const jar = cookies();
  const cookieToken = jar.get(CSRF_COOKIE)?.value;
  const headerToken = req.headers.get(CSRF_HEADER);
  const submitted = headerToken || bodyCsrf || undefined;
  if (!checkCsrf(cookieToken, submitted)) {
    throw new CsrfError("csrf token mismatch");
  }
}

export type LoginResult = {
  token: string;
  csrf: string;
  user: SessionUser;
};

export async function loginWithPassword(opts: {
  username: string;
  password: string;
  userAgent?: string | null;
  ipAddress?: string | null;
}): Promise<LoginResult | null> {
  if (isDemoMode()) {
    if (!checkPassword(opts.password)) return null;
    const username = opts.username || "reviewer";
    const token = await signSession(username);
    return {
      token,
      csrf: newCsrfToken(),
      user: {
        id: "demo-user",
        username,
        role: "admin",
        displayName: username,
      },
    };
  }

  const user = await verifyUserCredentials(opts.username, opts.password);
  if (!user) {
    await query(
      `
      INSERT INTO login_attempts (username, succeeded, ip_address, user_agent, failure_reason)
      VALUES ($1, FALSE, $2, $3, $4)
      `,
      [
        opts.username.trim(),
        opts.ipAddress ?? null,
        opts.userAgent ?? null,
        "invalid_credentials",
      ]
    ).catch(() => undefined);
    return null;
  }

  const token = await createPostgresSession(user.id, {
    userAgent: opts.userAgent,
    ipAddress: opts.ipAddress,
  });
  await query(
    `
    INSERT INTO login_attempts (username, succeeded, ip_address, user_agent)
    VALUES ($1, TRUE, $2, $3)
    `,
    [user.username, opts.ipAddress ?? null, opts.userAgent ?? null]
  ).catch(() => undefined);

  return { token, csrf: newCsrfToken(), user };
}

export async function logoutCurrentSession(): Promise<void> {
  const jar = cookies();
  const token = jar.get(SESSION_COOKIE)?.value;
  if (token && isPostgresMode()) {
    await revokePostgresSession(token);
  }
}

export { sessionCookieOptions, csrfCookieOptions, newCsrfToken, SESSION_COOKIE, CSRF_COOKIE };

/** List users (admin). */
export async function listUsers() {
  if (isDemoMode()) {
    return [
      {
        id: "demo-user",
        username: "reviewer",
        role: "admin" as StudioRole,
        active: true,
        display_name: "Demo admin",
      },
    ];
  }
  const { rows } = await query<{
    id: string;
    username: string;
    role: StudioRole;
    active: boolean;
    display_name: string | null;
    created_at: Date;
  }>(
    `
    SELECT id, username, role, active, display_name, created_at
    FROM users
    ORDER BY username
    `
  );
  return rows;
}

export async function recordAudit(opts: {
  actor: string;
  actorUserId?: string | null;
  action: string;
  entityType: string;
  entityId: string;
  beforeJson?: unknown;
  afterJson?: unknown;
  requestId?: string | null;
  ipAddress?: string | null;
}) {
  if (!isPostgresMode()) return;
  await query(
    `
    INSERT INTO audit_events (
      actor, actor_user_id, action, entity_type, entity_id,
      before_json, after_json, request_id, ip_address
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    `,
    [
      opts.actor,
      opts.actorUserId ?? null,
      opts.action,
      opts.entityType,
      opts.entityId,
      opts.beforeJson != null ? JSON.stringify(opts.beforeJson) : null,
      opts.afterJson != null ? JSON.stringify(opts.afterJson) : null,
      opts.requestId ?? null,
      opts.ipAddress ?? null,
    ]
  );
}

export { withTransaction };
