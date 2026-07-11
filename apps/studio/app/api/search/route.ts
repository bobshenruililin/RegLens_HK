import { NextResponse } from "next/server";
import { listDecisions } from "../../../lib/data";

function tokens(q: string): string[] {
  return (q.toLowerCase().match(/[a-z0-9_]{2,}/g) || []);
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const q = searchParams.get("q") || "";
  const regulator = searchParams.get("regulator");
  const profession = searchParams.get("profession");
  const propType = searchParams.get("prop_type");
  const terms = tokens(q);
  const hits: Array<Record<string, unknown>> = [];

  for (const decision of listDecisions()) {
    if (regulator && decision.regulator_code !== regulator) continue;
    if (profession && decision.profession !== profession) continue;
    for (const prop of decision.propositions) {
      if (!prop.published) continue;
      if (propType && prop.prop_type !== propType) continue;
      const hay = `${prop.claim_text}`.toLowerCase();
      const evidence = prop.evidence.map((e) => e.quote).join(" ").toLowerCase();
      if (terms.length && !terms.every((t) => hay.includes(t) || evidence.includes(t))) {
        continue;
      }
      hits.push({
        decision_id: decision.id,
        title: decision.title,
        regulator_code: decision.regulator_code,
        profession: decision.profession,
        prop_type: prop.prop_type,
        claim_text: prop.claim_text,
        page_no: prop.evidence[0]?.page_no ?? null,
        score: terms.reduce((acc, t) => acc + hay.split(t).length - 1, 1),
      });
    }
  }

  hits.sort((a, b) => Number(b.score) - Number(a.score));
  return NextResponse.json({
    query: q,
    semantic_enabled: false,
    hits: hits.slice(0, 50),
    notice:
      "Keyword and structured-field search over local seed only. Not PostgreSQL FTS. Semantic search is disabled.",
  });
}
