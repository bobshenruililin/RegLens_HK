import { NextResponse } from "next/server";
import {
  CSRF_COOKIE,
  SESSION_COOKIE,
  csrfCookieOptions,
  sessionCookieOptions,
} from "../../../lib/auth";
import { loginWithPassword } from "../../../lib/auth-server";
import { isPostgresMode } from "../../../lib/mode";

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as {
      password?: string;
      username?: string;
    };
    if (!body.password) {
      return NextResponse.json({ error: "invalid credentials" }, { status: 401 });
    }
    const username =
      body.username || (isPostgresMode() ? "" : "reviewer");
    if (isPostgresMode() && !username.trim()) {
      return NextResponse.json(
        { error: "username required in postgres mode" },
        { status: 400 }
      );
    }

    const result = await loginWithPassword({
      username: username || "reviewer",
      password: body.password,
      userAgent: req.headers.get("user-agent"),
      ipAddress:
        req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || null,
    });
    if (!result) {
      return NextResponse.json({ error: "invalid credentials" }, { status: 401 });
    }

    const res = NextResponse.json({
      ok: true,
      user: {
        username: result.user.username,
        role: result.user.role,
      },
    });
    res.cookies.set(SESSION_COOKIE, result.token, sessionCookieOptions());
    res.cookies.set(CSRF_COOKIE, result.csrf, csrfCookieOptions());
    return res;
  } catch (err) {
    const message = err instanceof Error ? err.message : "login failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
