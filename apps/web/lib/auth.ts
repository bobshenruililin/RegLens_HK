const COOKIE = "reglens_session";

function secret(): string {
  return process.env.REGLENS_SESSION_SECRET || "dev-only-reglens-secret-change-me";
}

function expectedPassword(): string {
  return process.env.AUTH_PASSWORD || "reglens-internal";
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
    return await crypto.subtle.verify(
      "HMAC",
      key,
      sigCopy,
      new TextEncoder().encode(payload)
    );
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
