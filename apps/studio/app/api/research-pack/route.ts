import { NextResponse } from "next/server";
import { buildResearchPack } from "../../../lib/research-data";

export async function POST(req: Request) {
  const body = (await req.json()) as { decision_ids?: unknown };
  if (!Array.isArray(body.decision_ids)) {
    return NextResponse.json({ error: "decision_ids must be an array" }, { status: 400 });
  }
  const decisionIds = body.decision_ids.filter(
    (item): item is string => typeof item === "string" && item.trim().length > 0
  );
  if (decisionIds.length === 0) {
    return NextResponse.json({ error: "select at least one decision" }, { status: 400 });
  }

  const pack = await buildResearchPack(decisionIds);
  return NextResponse.json(pack);
}
