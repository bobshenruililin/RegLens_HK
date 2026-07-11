import { NextResponse } from "next/server";
import {
  CSRF_COOKIE,
  csrfCookieOptions,
  newCsrfToken,
} from "../../../lib/auth";
import { getCurrentUser } from "../../../lib/auth-server";
import { isPostgresMode } from "../../../lib/mode";

/** Issue / rotate CSRF double-submit cookie (postgres mode). */
export async function GET() {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  if (!isPostgresMode()) {
    return NextResponse.json({
      csrf: null,
      mode: "demo",
      notice: "CSRF not required in demo mode",
    });
  }
  const token = newCsrfToken();
  const res = NextResponse.json({ csrf: token, mode: "postgres" });
  res.cookies.set(CSRF_COOKIE, token, csrfCookieOptions());
  return res;
}
