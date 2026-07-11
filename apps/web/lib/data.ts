import fs from "node:fs";
import path from "node:path";

export type EvidenceRef = {
  span_id: string | null;
  page_no: number;
  quote: string;
  char_start?: number | null;
  char_end?: number | null;
};

export type Proposition = {
  id: string;
  prop_type: string;
  epistemic_class: string;
  claim_text: string;
  confidence: number;
  review_status: string;
  published: boolean;
  evidence: EvidenceRef[];
};

export type DecisionRecord = {
  id: string;
  document_id: string;
  document_sha256: string;
  regulator_code: string;
  source_id: string;
  title: string;
  case_ref?: string | null;
  decision_date?: string | null;
  profession?: string | null;
  defendant_name_as_published?: string | null;
  defendant_registration_no?: string | null;
  source_url?: string | null;
  licence_notice?: string;
  coverage?: { missing_fields?: string[]; warnings?: string[] };
  pages: Array<{ span_id: string; page_no: number; text: string }>;
  propositions: Proposition[];
};

function roots(): string[] {
  const cwd = process.cwd();
  return [
    path.resolve(cwd, "../../data/seed"),
    path.resolve("/workspace/data/seed"),
    path.resolve(cwd, "../../fixtures/seed"),
    path.resolve("/workspace/fixtures/seed"),
  ];
}

export function loadDecision(id?: string): DecisionRecord | null {
  for (const root of roots()) {
    if (id) {
      const p = path.join(root, "decisions", `${id}.json`);
      if (fs.existsSync(p)) {
        return JSON.parse(fs.readFileSync(p, "utf8")) as DecisionRecord;
      }
    } else {
      const fallback = path.join(root, "decision.json");
      if (fs.existsSync(fallback)) {
        return JSON.parse(fs.readFileSync(fallback, "utf8")) as DecisionRecord;
      }
    }
  }
  return null;
}

export function listDecisions(): DecisionRecord[] {
  const seen = new Set<string>();
  const out: DecisionRecord[] = [];
  for (const root of roots()) {
    const dir = path.join(root, "decisions");
    if (!fs.existsSync(dir)) continue;
    for (const name of fs.readdirSync(dir)) {
      if (!name.endsWith(".json")) continue;
      const decision = JSON.parse(
        fs.readFileSync(path.join(dir, name), "utf8")
      ) as DecisionRecord;
      if (seen.has(decision.id)) continue;
      seen.add(decision.id);
      out.push(decision);
    }
  }
  return out;
}

function writableDecisionPath(id: string): string {
  for (const root of roots()) {
    const p = path.join(root, "decisions", `${id}.json`);
    if (fs.existsSync(p)) return p;
  }
  return path.resolve("/workspace/data/seed/decisions", `${id}.json`);
}

export function saveDecision(decision: DecisionRecord): void {
  const target = writableDecisionPath(decision.id);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, JSON.stringify(decision, null, 2), "utf8");
  const root = path.dirname(path.dirname(target));
  fs.writeFileSync(
    path.join(root, "decision.json"),
    JSON.stringify(decision, null, 2),
    "utf8"
  );
}

export function canPublish(review_status: string, evidence: unknown[]): boolean {
  if (review_status !== "accepted" && review_status !== "edited") return false;
  return Array.isArray(evidence) && evidence.length > 0;
}
