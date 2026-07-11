/** RegLens Studio storage mode: demo (file seed) | postgres (DATABASE_URL). */

export type RegLensMode = "demo" | "postgres";

export function getMode(): RegLensMode {
  const raw = (process.env.REGLENS_MODE || "").trim().toLowerCase();
  if (!raw) return "demo";
  if (raw === "demo" || raw === "postgres") return raw;
  throw new Error(`Invalid REGLENS_MODE=${raw}; expected demo|postgres`);
}

export function isPostgresMode(): boolean {
  return getMode() === "postgres";
}

export function isDemoMode(): boolean {
  return getMode() === "demo";
}

/**
 * Return DATABASE_URL. Fail closed when REGLENS_MODE=postgres and DSN missing.
 */
export function requireDatabaseUrl(): string {
  const dsn = (process.env.DATABASE_URL || "").trim();
  if (isPostgresMode() && !dsn) {
    throw new Error(
      "REGLENS_MODE=postgres requires DATABASE_URL (fail-closed; refusing to continue)"
    );
  }
  if (!dsn) {
    throw new Error("DATABASE_URL is required but empty or unset");
  }
  return dsn;
}
