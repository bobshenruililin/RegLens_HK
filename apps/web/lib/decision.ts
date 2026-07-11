import fs from "node:fs";
import path from "node:path";

export type DecisionSeed = {
  id: string;
  title: string;
  regulator_code: string;
  case_ref?: string | null;
  decision_date?: string | null;
  profession?: string | null;
  defendant_name_as_published?: string | null;
  defendant_registration_no?: string | null;
  source_url?: string | null;
  licence_notice?: string;
  coverage?: { missing_fields?: string[]; warnings?: string[] };
  pages: Array<{ span_id: string; page_no: number; text: string }>;
  propositions: Array<{
    id: string;
    prop_type: string;
    epistemic_class: string;
    claim_text: string;
    confidence: number;
    review_status: string;
    published: boolean;
    evidence: Array<{
      span_id: string | null;
      page_no: number;
      quote: string;
    }>;
  }>;
};

function candidates(): string[] {
  const cwd = process.cwd();
  return [
    path.resolve(cwd, "../../data/seed/decision.json"),
    path.resolve(cwd, "../../../data/seed/decision.json"),
    path.resolve(cwd, "data/seed/decision.json"),
    path.resolve("/workspace/data/seed/decision.json"),
    path.resolve(cwd, "../../fixtures/seed/decision.json"),
    path.resolve("/workspace/fixtures/seed/decision.json"),
  ];
}

export function loadDecision(id?: string): DecisionSeed | null {
  if (id) {
    const byId = [
      path.resolve(process.cwd(), `../../data/seed/decisions/${id}.json`),
      path.resolve(process.cwd(), `data/seed/decisions/${id}.json`),
      path.resolve("/workspace/data/seed/decisions", `${id}.json`),
      path.resolve(process.cwd(), `../../fixtures/seed/decisions/${id}.json`),
      path.resolve("/workspace/fixtures/seed/decisions", `${id}.json`),
    ];
    for (const p of byId) {
      if (fs.existsSync(p)) {
        return JSON.parse(fs.readFileSync(p, "utf8")) as DecisionSeed;
      }
    }
  }
  for (const p of candidates()) {
    if (fs.existsSync(p)) {
      return JSON.parse(fs.readFileSync(p, "utf8")) as DecisionSeed;
    }
  }
  return null;
}
