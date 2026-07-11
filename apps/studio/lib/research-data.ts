import fs from "node:fs";
import path from "node:path";
import { listDecisions, type DecisionRecord, type Proposition } from "./data";
import { isPostgresMode } from "./mode";
import {
  listDecisionNavigationPg,
  listResearchAnnotationsPg,
  listResearchPropositionsPg,
  listSourceSyncStatusPg,
  type SourceSyncStatusRow,
} from "./pg-data";

export type TaxonomyCategory = {
  code: string;
  label: string;
};

export type Taxonomy = {
  taxonomy_version: string;
  issue_categories: TaxonomyCategory[];
  finding_outcomes: TaxonomyCategory[];
  sanction_categories: TaxonomyCategory[];
  factor_categories: TaxonomyCategory[];
};

export type ResearchAnnotation = {
  decision_id: string | null;
  external_ref: string;
  regulator_code: string;
  profession: string | null;
  title: string | null;
  issue_categories: string[];
  finding_outcomes: string[];
  sanction_categories: string[];
  factor_categories: string[];
  summary: string;
  takeaway: string;
  supporting_client_refs: string[];
  reviewer_status: string;
};

export type ResearchDecisionOption = {
  id: string;
  external_ref: string;
  title: string;
  regulator_code: string;
  profession?: string | null;
};

export type ResearchProposition = {
  decision_id: string;
  external_ref: string;
  title: string;
  regulator_code: string;
  profession?: string | null;
  client_ref: string;
  prop_type: string;
  epistemic_class: string;
  claim_text: string;
  review_status: string | null;
  evidence: Array<{ page_no: number; quote: string }>;
};

export type IssueDetail = {
  category: TaxonomyCategory | null;
  decisions: ResearchAnnotation[];
};

export type SanctionRow = TaxonomyCategory & {
  decision_count: number;
  decisions: ResearchAnnotation[];
  propositions: ResearchProposition[];
};

export type SyncStatus = {
  mode: "demo" | "postgres";
  message: string;
  rows: SourceSyncStatusRow[];
};

type EditorialAnnotationsFile = {
  taxonomy_version: string;
  annotations: Array<{
    external_ref: string;
    regulator_code: string;
    issue_categories: string[];
    finding_outcomes: string[];
    sanction_categories: string[];
    factor_categories: string[];
    editorial_note: {
      summary: string;
      takeaway: string;
      supporting_client_refs: string[];
      reviewer_status: string;
    };
  }>;
};

function firstExistingPath(...relativeParts: string[]): string | null {
  const candidates = [
    path.resolve(process.cwd(), "../../", ...relativeParts),
    path.resolve("/workspace", ...relativeParts),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}

function readJson<T>(...relativeParts: string[]): T | null {
  const target = firstExistingPath(...relativeParts);
  if (!target) return null;
  return JSON.parse(fs.readFileSync(target, "utf8")) as T;
}

function externalRef(decision: DecisionRecord): string {
  const loose = decision as DecisionRecord & { case_refs?: string[] };
  return decision.case_ref || loose.case_refs?.[0] || decision.id;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function reviewed(prop: Proposition): boolean {
  return prop.published || prop.review_status === "accepted" || prop.review_status === "edited";
}

function titleFor(decision: DecisionRecord): string {
  return decision.title || externalRef(decision);
}

function csvEscape(value: unknown): string {
  const text = String(value ?? "");
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function loadTaxonomy(): Taxonomy {
  const taxonomy = readJson<Taxonomy>("publications", "taxonomy", "taxonomy.v1.json");
  if (!taxonomy) {
    return {
      taxonomy_version: "unknown",
      issue_categories: [],
      finding_outcomes: [],
      sanction_categories: [],
      factor_categories: [],
    };
  }
  return taxonomy;
}

export async function listResearchAnnotations(): Promise<ResearchAnnotation[]> {
  if (isPostgresMode()) {
    const rows = await listResearchAnnotationsPg();
    return rows.map((row) => ({
      decision_id: row.decision_id,
      external_ref: row.external_ref,
      regulator_code: row.regulator_code,
      profession: row.profession,
      title: row.title,
      issue_categories: asStringArray(row.issue_categories),
      finding_outcomes: asStringArray(row.finding_outcomes),
      sanction_categories: asStringArray(row.sanction_categories),
      factor_categories: asStringArray(row.factor_categories),
      summary: row.summary,
      takeaway: row.takeaway,
      supporting_client_refs: asStringArray(row.supporting_client_refs),
      reviewer_status: row.reviewer_status,
    }));
  }

  const annotations = readJson<EditorialAnnotationsFile>(
    "publications",
    "demo",
    "editorial_annotations.v1.json"
  );
  const decisions = listDecisions();
  return (annotations?.annotations || []).map((annotation) => {
    const decision = decisions.find((item) => externalRef(item) === annotation.external_ref);
    return {
      decision_id: decision?.id ?? null,
      external_ref: annotation.external_ref,
      regulator_code: annotation.regulator_code,
      profession: decision?.profession ?? null,
      title: decision?.title ?? null,
      issue_categories: annotation.issue_categories,
      finding_outcomes: annotation.finding_outcomes,
      sanction_categories: annotation.sanction_categories,
      factor_categories: annotation.factor_categories,
      summary: annotation.editorial_note.summary,
      takeaway: annotation.editorial_note.takeaway,
      supporting_client_refs: annotation.editorial_note.supporting_client_refs,
      reviewer_status: annotation.editorial_note.reviewer_status,
    };
  });
}

export async function listResearchDecisionOptions(): Promise<ResearchDecisionOption[]> {
  if (isPostgresMode()) {
    const rows = await listDecisionNavigationPg();
    return rows.map((row) => ({
      id: row.id,
      external_ref: row.external_ref,
      title: row.title || row.external_ref,
      regulator_code: row.regulator_code,
      profession: row.profession,
    }));
  }

  return listDecisions().map((decision) => ({
    id: decision.id,
    external_ref: externalRef(decision),
    title: titleFor(decision),
    regulator_code: decision.regulator_code,
    profession: decision.profession,
  }));
}

export async function listIssueIndex(): Promise<Array<TaxonomyCategory & { decision_count: number }>> {
  const taxonomy = loadTaxonomy();
  const annotations = await listResearchAnnotations();
  return taxonomy.issue_categories.map((issue) => ({
    ...issue,
    decision_count: annotations.filter((annotation) =>
      annotation.issue_categories.includes(issue.code)
    ).length,
  }));
}

export async function getIssueDetail(code: string): Promise<IssueDetail> {
  const taxonomy = loadTaxonomy();
  const annotations = await listResearchAnnotations();
  return {
    category: taxonomy.issue_categories.find((issue) => issue.code === code) || null,
    decisions: annotations.filter((annotation) => annotation.issue_categories.includes(code)),
  };
}

export async function listResearchPropositions(
  decisionIds?: string[]
): Promise<ResearchProposition[]> {
  if (isPostgresMode()) {
    const rows = await listResearchPropositionsPg(decisionIds);
    return rows.map((row) => ({
      decision_id: row.decision_id,
      external_ref: row.external_ref,
      title: row.title || row.external_ref,
      regulator_code: row.regulator_code,
      profession: row.profession,
      client_ref: row.client_ref,
      prop_type: row.prop_type,
      epistemic_class: row.epistemic_class,
      claim_text: row.claim_text,
      review_status: row.latest_review_status,
      evidence: row.evidence.map((ev) => ({
        page_no: ev.page_no,
        quote: ev.quote_text,
      })),
    }));
  }

  return listDecisions()
    .filter((decision) => !decisionIds || decisionIds.includes(decision.id))
    .flatMap((decision) =>
      decision.propositions.filter(reviewed).map((prop) => ({
        decision_id: decision.id,
        external_ref: externalRef(decision),
        title: titleFor(decision),
        regulator_code: decision.regulator_code,
        profession: decision.profession,
        client_ref:
          "client_ref" in prop && typeof prop.client_ref === "string"
            ? prop.client_ref
            : prop.id,
        prop_type: prop.prop_type,
        epistemic_class: prop.epistemic_class,
        claim_text: prop.claim_text,
        review_status: prop.review_status,
        evidence: prop.evidence.map((ev) => ({
          page_no: ev.page_no,
          quote: ev.quote,
        })),
      }))
    );
}

export async function listSanctionIndex(): Promise<SanctionRow[]> {
  const taxonomy = loadTaxonomy();
  const annotations = await listResearchAnnotations();
  const propositions = (await listResearchPropositions()).filter((prop) =>
    ["sanction", "costs"].includes(prop.prop_type)
  );
  return taxonomy.sanction_categories.map((sanction) => {
    const decisions = annotations.filter((annotation) =>
      annotation.sanction_categories.includes(sanction.code)
    );
    return {
      ...sanction,
      decision_count: decisions.length,
      decisions,
      propositions: propositions.filter((prop) =>
        decisions.some((decision) => decision.external_ref === prop.external_ref)
      ),
    };
  });
}

export async function listAuthoritiesIndex(): Promise<ResearchProposition[]> {
  return (await listResearchPropositions()).filter((prop) =>
    ["rule", "legal_test", "authority"].includes(prop.prop_type)
  );
}

export async function getSyncStatus(): Promise<SyncStatus> {
  if (!isPostgresMode()) {
    return {
      mode: "demo",
      message:
        "Demo mode uses local seed files. No live source sync state is recorded in Studio.",
      rows: [],
    };
  }
  const rows = await listSourceSyncStatusPg();
  return {
    mode: "postgres",
    message: rows.length
      ? "Source sync status from source_collections, documents, and worker jobs."
      : "Postgres is configured but no source collections are present.",
    rows,
  };
}

export async function buildResearchPack(decisionIds: string[]): Promise<{
  markdown: string;
  csv: string;
  decision_count: number;
}> {
  const selected = decisionIds.filter(Boolean);
  const options = await listResearchDecisionOptions();
  const optionById = new Map(options.map((option) => [option.id, option]));
  const selectedOptions = selected
    .map((id) => optionById.get(id))
    .filter((option): option is ResearchDecisionOption => Boolean(option));
  const annotations = await listResearchAnnotations();
  const propositions = await listResearchPropositions(selected);

  const markdown: string[] = [
    "# RegLens HK research pack",
    "",
    `Decision count: ${selectedOptions.length}`,
    `Storage mode: ${isPostgresMode() ? "postgres" : "demo"}`,
    "",
    "Primary sources remain authoritative. This export is an internal research aid and is not legal advice.",
    "",
  ];

  for (const option of selectedOptions) {
    const annotation = annotations.find(
      (item) => item.decision_id === option.id || item.external_ref === option.external_ref
    );
    const props = propositions.filter((prop) => prop.decision_id === option.id);
    markdown.push(`## ${option.title}`, "");
    markdown.push(`- Regulator: ${option.regulator_code}`);
    markdown.push(`- External ref: ${option.external_ref}`);
    if (option.profession) markdown.push(`- Profession: ${option.profession}`);
    if (annotation) {
      markdown.push(`- Issues: ${annotation.issue_categories.join(", ") || "none"}`);
      markdown.push(`- Findings: ${annotation.finding_outcomes.join(", ") || "none"}`);
      markdown.push(`- Sanctions: ${annotation.sanction_categories.join(", ") || "none"}`);
      markdown.push(`- Factors: ${annotation.factor_categories.join(", ") || "none"}`);
      markdown.push("", `**Summary:** ${annotation.summary}`, "");
      markdown.push(`**Takeaway:** ${annotation.takeaway}`, "");
    }
    markdown.push("| Type | Status | Claim | Evidence |");
    markdown.push("| --- | --- | --- | --- |");
    for (const prop of props) {
      markdown.push(
        `| ${prop.prop_type} | ${prop.review_status || "none"} | ${prop.claim_text.replaceAll("|", "\\|")} | ${prop.evidence
          .map((ev) => `p.${ev.page_no}: ${ev.quote}`)
          .join("; ")
          .replaceAll("|", "\\|")} |`
      );
    }
    markdown.push("");
  }

  const csvRows = [
    [
      "decision_id",
      "external_ref",
      "regulator_code",
      "title",
      "prop_type",
      "client_ref",
      "review_status",
      "claim_text",
      "evidence",
    ],
    ...propositions.map((prop) => [
      prop.decision_id,
      prop.external_ref,
      prop.regulator_code,
      prop.title,
      prop.prop_type,
      prop.client_ref,
      prop.review_status || "",
      prop.claim_text,
      prop.evidence.map((ev) => `p.${ev.page_no}: ${ev.quote}`).join(" | "),
    ]),
  ];

  return {
    markdown: markdown.join("\n"),
    csv: csvRows.map((row) => row.map(csvEscape).join(",")).join("\n"),
    decision_count: selectedOptions.length,
  };
}
