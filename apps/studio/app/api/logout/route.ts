import { NextResponse } from "next/server";
import { CSRF_COOKIE, SESSION_COOKIE } from "../../../lib/auth";
import { logoutCurrentSession } from "../../../lib/auth-server";

export async function POST() {
  try {
    await logoutCurrentSession();
  } catch {
    /* best-effort revoke */
  }
  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE, "", {
    httpOnly: true,
    path: "/",
    maxAge: 0,
  });
  res.cookies.set(CSRF_COOKIE, "", { path: "/", maxAge: 0 });
  return res;
}
