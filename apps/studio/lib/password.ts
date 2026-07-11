import { randomBytes, scryptSync, timingSafeEqual } from "node:crypto";

/** OWASP-aligned scrypt parameters (match Python reglens_worker.pg.users). */
const SCRYPT_N = 2 ** 14;
const SCRYPT_R = 8;
const SCRYPT_P = 1;
const SCRYPT_DKLEN = 64;
const SALT_BYTES = 16;

/**
 * Hash password to Python-compatible format:
 * `scrypt$N$r$p$salt_b64$hash_b64`
 */
export function hashPassword(password: string): string {
  if (!password) throw new Error("password must be non-empty");
  const salt = randomBytes(SALT_BYTES);
  const digest = scryptSync(password, salt, SCRYPT_DKLEN, {
    N: SCRYPT_N,
    r: SCRYPT_R,
    p: SCRYPT_P,
  });
  return `scrypt$${SCRYPT_N}$${SCRYPT_R}$${SCRYPT_P}$${salt.toString("base64")}$${digest.toString("base64")}`;
}

/** Verify password against stored `scrypt$N$r$p$salt_b64$hash_b64`. */
export function verifyPassword(password: string, stored: string): boolean {
  const parts = stored.split("$");
  if (parts.length !== 6) return false;
  const [algo, nS, rS, pS, saltB64, hashB64] = parts;
  if (algo !== "scrypt") return false;
  try {
    const n = Number(nS);
    const r = Number(rS);
    const p = Number(pS);
    const salt = Buffer.from(saltB64, "base64");
    const expected = Buffer.from(hashB64, "base64");
    const actual = scryptSync(password, salt, expected.length, { N: n, r, p });
    if (actual.length !== expected.length) return false;
    return timingSafeEqual(actual, expected);
  } catch {
    return false;
  }
}
