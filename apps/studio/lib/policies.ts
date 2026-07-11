import fs from "node:fs";
import path from "node:path";
import { listDecisions } from "./data";
import { isDemoMode } from "./mode";

export type SourcePolicyFile = {
  schema_version?: string;
  policies: Array<{
    source_id: string;
    regulator_code: string;
    visibility: string;
    max_excerpt_chars: number;
    attribution_required: boolean;
    notes?: string;
  }>;
};

function policyRoots(): string[] {
  const cwd = process.cwd();
  return [
    path.resolve(cwd, "../../publications/policies"),
    path.resolve("/workspace/publications/policies"),
  ];
}

/** Read-only source publication policies from JSON (demo) or caller supplies DB rows. */
export function loadSourcePoliciesFromFile(): SourcePolicyFile | null {
  for (const root of policyRoots()) {
    const p = path.join(root, "source_publication_policy.v1.json");
    if (fs.existsSync(p)) {
      return JSON.parse(fs.readFileSync(p, "utf8")) as SourcePolicyFile;
    }
  }
  return null;
}

export function demoDashboardCounts() {
  const decisions = listDecisions();
  const pending = decisions.reduce(
    (n, d) =>
      n +
      d.propositions.filter(
        (p) => !p.published && p.review_status !== "rejected"
      ).length,
    0
  );
  const published = decisions.reduce(
    (n, d) => n + d.propositions.filter((p) => p.published).length,
    0
  );
  return {
    decisions: decisions.length,
    documents: decisions.length,
    jobsPending: 0,
    jobsRunning: 0,
    reviewsPending: pending,
    releases: 0,
    auditEvents: 0,
    publishedPropositions: published,
    mode: isDemoMode() ? "demo" : "postgres",
  };
}
