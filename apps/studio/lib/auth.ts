const COOKIE = "reglens_session";
const MAX_AGE_MS = 12 * 60 * 60 * 1000; // 12 hours

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

function expectedPassword(): string {
  const value = process.env.AUTH_PASSWORD;
  if (!value) {
    if (isProduction()) {
      throw new Error(
        "AUTH_PASSWORD is required in production (Studio fail-closed)"
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

export async function signSession(username: string): Promise<string> {
  const payload = b64url(
    new TextEncoder().encode(JSON.stringify({ u: username, t: Date.now() }))
  );
  const key = await hmacKey();
  const sig = b64url(
    await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(payload))
  );
  return `${payload}.${sig}`;
}

export async function verifySessionToken(
  token: string | undefined
): Promise<boolean> {
  if (!token || !token.includes(".")) return false;
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
  return COOKIE;
}
