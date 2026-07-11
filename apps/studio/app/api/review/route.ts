import { NextResponse } from "next/server";
import { canPublish, listDecisions, loadDecision, saveDecision } from "../../../lib/data";

export async function GET() {
  const items = [];
  for (const decision of listDecisions()) {
    for (const prop of decision.propositions) {
      if (prop.published) continue;
      if (prop.review_status === "rejected") continue;
      items.push({
        decision_id: decision.id,
        decision_title: decision.title,
        regulator_code: decision.regulator_code,
        proposition: prop,
      });
    }
  }
  return NextResponse.json({ items });
}

export async function POST(req: Request) {
  const body = (await req.json()) as {
    decision_id: string;
    proposition_id: string;
    review_status: "pending" | "accepted" | "edited" | "rejected";
    claim_text?: string;
  };
  const decision = loadDecision(body.decision_id);
  if (!decision) {
    return NextResponse.json({ error: "decision not found" }, { status: 404 });
  }
  const prop = decision.propositions.find((p) => p.id === body.proposition_id);
  if (!prop) {
    return NextResponse.json({ error: "proposition not found" }, { status: 404 });
  }
  if (body.claim_text !== undefined) {
    prop.claim_text = body.claim_text;
    if (body.review_status === "accepted") {
      body.review_status = "edited";
    }
  }
  prop.review_status = body.review_status;
  if (body.review_status === "accepted" || body.review_status === "edited") {
    if (!canPublish(prop.review_status, prop.evidence)) {
      return NextResponse.json(
        { error: "cannot publish without evidence spans and accept/edit review" },
        { status: 400 }
      );
    }
    prop.published = true;
  } else {
    prop.published = false;
  }
  saveDecision(decision);
  return NextResponse.json({ ok: true, proposition: prop });
}
