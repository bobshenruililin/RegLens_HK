import { NextResponse } from "next/server";
import { checkPassword, sessionCookieName, signSession } from "../../../lib/auth";

export async function POST(req: Request) {
  const body = (await req.json()) as { password?: string; username?: string };
  if (!body.password || !checkPassword(body.password)) {
    return NextResponse.json({ error: "invalid credentials" }, { status: 401 });
  }
  const token = await signSession(body.username || "reviewer");
  const res = NextResponse.json({ ok: true });
  res.cookies.set(sessionCookieName(), token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: process.env.NODE_ENV === "production",
  });
  return res;
}
