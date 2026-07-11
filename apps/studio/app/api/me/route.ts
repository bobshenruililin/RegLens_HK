import { NextResponse } from "next/server";
import { getCurrentUser } from "../../../lib/auth-server";
import { getMode } from "../../../lib/mode";

export async function GET() {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  return NextResponse.json({
    mode: getMode(),
    user: {
      id: user.id,
      username: user.username,
      role: user.role,
      displayName: user.displayName,
    },
  });
}
