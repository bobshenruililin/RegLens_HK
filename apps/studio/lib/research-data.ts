import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
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
  source_id?: string | null;
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

export type ResearchDecisionSummary = ResearchAnnotation & {
  id: string | null;
  year: string | null;
  propositions: ResearchProposition[];
  charge: ResearchProposition | null;
  finding: ResearchProposition | null;
  sanction: ResearchProposition | null;
};

export type ResearchExploreFilters = {
  regulator?: string;
  year?: string;
  issue?: string;
  prop_type?: string;
  q?: string;
};

export type ResearchFacets = {
  regulators: string[];
  years: string[];
  issues: TaxonomyCategory[];
  prop_types: string[];
};

export type ResearchHomeCounts = {
  decisions: number;
  propositions: number;
  regulators: number;
  issues: number;
  sanctions: number;
  authorities: number;
};

export type Core10PilotSlot = {
  source_item_id: string;
  external_ref: string;
  source_id: string;
  case_ref: string;
  rationale: string;
  issue_targets: string[];
  multi_charge: boolean;
  inclusion_status: "planned" | "included" | "blocked";
  acquisition_status: string;
  extraction_status: string;
  critic_status: string;
  review_status: string;
  completeness_status: string;
  second_check_status: string;
  notes: string;
};

export type Core10PilotSpec = {
  schema_version: string;
  spec_id: string;
  title: string;
  purpose: string;
  source_kind: string;
  planned_total: number;
  statistical_note: string;
  operator_note: string;
  slots: Core10PilotSlot[];
};

export type Core10Progress = {
  spec: Core10PilotSpec;
  slots: Array<Core10PilotSlot & { reviewed_decision: ResearchDecisionSummary | null }>;
  counts: {
    planned: number;
    included: number;
    blocked: number;
    acquired: number;
    extracted: number;
    critic_ready: number;
    reviewed: number;
    complete: number;
    second_checked: number;
    real_reviewed_decisions: number;
  };
};

export type ResearchCollection = {
  id: string;
  title: string;
  description: string;
  decision_ids: string[];
  created_at: string;
  updated_at: string;
  notes?: string;
  synthetic_only: boolean;
};

export type ResearchCollectionExport = {
  collection: ResearchCollection;
  markdown: string;
  csv: string;
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

function workspaceRoot(): string {
  const fromStudio = path.resolve(process.cwd(), "../../");
  if (fs.existsSync(path.join(fromStudio, "apps", "studio"))) {
    return fromStudio;
  }
  return fs.existsSync("/workspace") ? "/workspace" : process.cwd();
}

function yearFromText(...values: Array<string | null | undefined>): string | null {
  for (const value of values) {
    const match = value?.match(/\b(19|20)\d{2}\b/);
    if (match) return match[0];
  }
  return null;
}

function isSyntheticExternalRef(externalRef: string): boolean {
  return externalRef.startsWith("SYN-");
}

function statusDone(status: string, done: string[] = ["done", "complete"]): boolean {
  const normalized = status.toLowerCase();
  return done.some((item) => normalized.includes(item));
}

function collectionRoot(): string {
  return (
    firstExistingPath("data", "research-collections") ||
    path.join(workspaceRoot(), "data", "research-collections")
  );
}

function assertSafeCollectionId(id: string): void {
  if (!/^[a-zA-Z0-9_.-]+$/.test(id)) {
    throw new Error("invalid collection id");
  }
}

function collectionPath(id: string): string {
  assertSafeCollectionId(id);
  return path.join(collectionRoot(), `${id}.json`);
}

function slugify(value: string): string {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 48) || "research-collection"
  );
}

function normalizeCollection(raw: unknown): ResearchCollection | null {
  if (!raw || typeof raw !== "object") return null;
  const item = raw as Partial<ResearchCollection>;
  if (
    typeof item.id !== "string" ||
    typeof item.title !== "string" ||
    !Array.isArray(item.decision_ids)
  ) {
    return null;
  }
  return {
    id: item.id,
    title: item.title,
    description: typeof item.description === "string" ? item.description : "",
    decision_ids: item.decision_ids.filter(
      (decisionId): decisionId is string => typeof decisionId === "string"
    ),
    created_at: typeof item.created_at === "string" ? item.created_at : new Date(0).toISOString(),
    updated_at: typeof item.updated_at === "string" ? item.updated_at : new Date(0).toISOString(),
    notes: typeof item.notes === "string" ? item.notes : undefined,
    synthetic_only: item.synthetic_only !== false,
  };
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
      source_id: row.source_id,
    }));
  }

  return listDecisions().map((decision) => ({
    id: decision.id,
    external_ref: externalRef(decision),
    title: titleFor(decision),
    regulator_code: decision.regulator_code,
    profession: decision.profession,
    source_id: decision.source_id,
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

export async function listRulesIndex(): Promise<ResearchProposition[]> {
  return (await listResearchPropositions()).filter((prop) =>
    ["rule", "legal_test"].includes(prop.prop_type)
  );
}

export async function listCitedAuthoritiesIndex(): Promise<ResearchProposition[]> {
  return (await listResearchPropositions()).filter((prop) => prop.prop_type === "authority");
}

export async function listReviewedResearchDecisions(): Promise<ResearchDecisionSummary[]> {
  const [annotations, options, propositions] = await Promise.all([
    listResearchAnnotations(),
    listResearchDecisionOptions(),
    listResearchPropositions(),
  ]);
  const byExternalRef = new Map(options.map((option) => [option.external_ref, option]));
  const byId = new Map(options.map((option) => [option.id, option]));

  return annotations
    .map((annotation) => {
      const option =
        (annotation.decision_id ? byId.get(annotation.decision_id) : undefined) ||
        byExternalRef.get(annotation.external_ref);
      const decisionProps = propositions.filter(
        (prop) =>
          prop.external_ref === annotation.external_ref ||
          (annotation.decision_id != null && prop.decision_id === annotation.decision_id)
      );
      return {
        ...annotation,
        id: annotation.decision_id,
        title: annotation.title || option?.title || annotation.external_ref,
        profession: annotation.profession || option?.profession || null,
        year: yearFromText(annotation.external_ref, option?.title),
        propositions: decisionProps,
        charge: decisionProps.find((prop) => prop.prop_type === "charge") || null,
        finding: decisionProps.find((prop) => prop.prop_type === "finding") || null,
        sanction: decisionProps.find((prop) => prop.prop_type === "sanction") || null,
      };
    })
    .sort((a, b) =>
      `${a.regulator_code}:${a.external_ref}`.localeCompare(
        `${b.regulator_code}:${b.external_ref}`
      )
    );
}

export async function getResearchHomeCounts(): Promise<ResearchHomeCounts> {
  const [decisions, propositions, taxonomy] = await Promise.all([
    listReviewedResearchDecisions(),
    listResearchPropositions(),
    Promise.resolve(loadTaxonomy()),
  ]);
  return {
    decisions: decisions.length,
    propositions: propositions.length,
    regulators: new Set(decisions.map((decision) => decision.regulator_code)).size,
    issues: taxonomy.issue_categories.filter((issue) =>
      decisions.some((decision) => decision.issue_categories.includes(issue.code))
    ).length,
    sanctions: taxonomy.sanction_categories.filter((sanction) =>
      decisions.some((decision) => decision.sanction_categories.includes(sanction.code))
    ).length,
    authorities: propositions.filter((prop) =>
      ["rule", "legal_test", "authority"].includes(prop.prop_type)
    ).length,
  };
}

export async function getResearchFacets(): Promise<ResearchFacets> {
  const [decisions, propositions, taxonomy] = await Promise.all([
    listReviewedResearchDecisions(),
    listResearchPropositions(),
    Promise.resolve(loadTaxonomy()),
  ]);
  return {
    regulators: [...new Set(decisions.map((decision) => decision.regulator_code))].sort(),
    years: [
      ...new Set(
        decisions
          .map((decision) => decision.year)
          .filter((year): year is string => Boolean(year))
      ),
    ].sort((a, b) => b.localeCompare(a)),
    issues: taxonomy.issue_categories,
    prop_types: [...new Set(propositions.map((prop) => prop.prop_type))].sort(),
  };
}

export function filterResearchDecisions(
  decisions: ResearchDecisionSummary[],
  filters: ResearchExploreFilters
): ResearchDecisionSummary[] {
  const q = filters.q?.trim().toLowerCase();
  return decisions.filter((decision) => {
    if (filters.regulator && decision.regulator_code !== filters.regulator) return false;
    if (filters.year && decision.year !== filters.year) return false;
    if (filters.issue && !decision.issue_categories.includes(filters.issue)) return false;
    if (
      filters.prop_type &&
      !decision.propositions.some((prop) => prop.prop_type === filters.prop_type)
    ) {
      return false;
    }
    if (!q) return true;
    const haystack = [
      decision.external_ref,
      decision.title,
      decision.summary,
      decision.takeaway,
      ...decision.issue_categories,
      ...decision.finding_outcomes,
      ...decision.sanction_categories,
      ...decision.propositions.map((prop) => prop.claim_text),
    ]
      .join(" ")
      .toLowerCase();
    return q
      .split(/\s+/)
      .filter(Boolean)
      .every((term) => haystack.includes(term));
  });
}

export async function listResearchExploreResults(
  filters: ResearchExploreFilters = {}
): Promise<ResearchDecisionSummary[]> {
  return filterResearchDecisions(await listReviewedResearchDecisions(), filters);
}

export async function getResearchDecisionSummaries(
  decisionIds: string[]
): Promise<ResearchDecisionSummary[]> {
  const wanted = new Set(decisionIds.filter(Boolean).slice(0, 4));
  if (wanted.size === 0) return [];
  return (await listReviewedResearchDecisions()).filter(
    (decision) =>
      (decision.id != null && wanted.has(decision.id)) || wanted.has(decision.external_ref)
  );
}

export async function getCoverageRows(): Promise<
  Array<ResearchDecisionSummary & { missing_surfaces: string[]; reviewed_prop_count: number }>
> {
  return (await listReviewedResearchDecisions()).map((decision) => {
    const types = new Set(decision.propositions.map((prop) => prop.prop_type));
    return {
      ...decision,
      missing_surfaces: ["charge", "finding", "sanction"].filter((type) => !types.has(type)),
      reviewed_prop_count: decision.propositions.length,
    };
  });
}

export function loadCore10Spec(): Core10PilotSpec {
  const spec = readJson<Core10PilotSpec>("publications", "pilot", "core10.v1.json");
  if (spec) return spec;
  return {
    schema_version: "unknown",
    spec_id: "core10.v1",
    title: "Core 10 pilot",
    purpose: "Core 10 pilot spec is missing.",
    source_kind: "synthetic_placeholders",
    planned_total: 10,
    statistical_note: "Core 10 is not representative.",
    operator_note: "Create publications/pilot/core10.v1.json before using this page.",
    slots: [],
  };
}

export async function getCore10Progress(): Promise<Core10Progress> {
  const spec = loadCore10Spec();
  const decisions = await listReviewedResearchDecisions();
  const decisionByExternalRef = new Map(decisions.map((decision) => [decision.external_ref, decision]));
  const slots = spec.slots.map((slot) => ({
    ...slot,
    reviewed_decision:
      decisionByExternalRef.get(slot.external_ref) ||
      decisionByExternalRef.get(slot.case_ref) ||
      null,
  }));
  return {
    spec,
    slots,
    counts: {
      planned: spec.slots.filter((slot) => slot.inclusion_status === "planned").length,
      included: spec.slots.filter((slot) => slot.inclusion_status === "included").length,
      blocked: spec.slots.filter((slot) => slot.inclusion_status === "blocked").length,
      acquired: spec.slots.filter((slot) => statusDone(slot.acquisition_status, ["done", "acquired"])).length,
      extracted: spec.slots.filter((slot) => statusDone(slot.extraction_status, ["done", "extracted"])).length,
      critic_ready: spec.slots.filter((slot) => statusDone(slot.critic_status, ["done", "passed", "ready"])).length,
      reviewed: spec.slots.filter((slot) => statusDone(slot.review_status, ["done", "reviewed", "accepted", "edited"])).length,
      complete: spec.slots.filter((slot) => statusDone(slot.completeness_status, ["done", "complete"])).length,
      second_checked: spec.slots.filter((slot) => statusDone(slot.second_check_status, ["done", "checked"])).length,
      real_reviewed_decisions: decisions.filter(
        (decision) => !isSyntheticExternalRef(decision.external_ref)
      ).length,
    },
  };
}

export async function getCore10Slot(
  id: string
): Promise<(Core10PilotSlot & { reviewed_decision: ResearchDecisionSummary | null }) | null> {
  const progress = await getCore10Progress();
  return (
    progress.slots.find(
      (slot) =>
        slot.source_item_id === id ||
        slot.external_ref === id ||
        slot.case_ref === id ||
        slot.reviewed_decision?.id === id
    ) || null
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

export async function listResearchCollections(): Promise<ResearchCollection[]> {
  const root = collectionRoot();
  if (!fs.existsSync(root)) return [];
  return fs
    .readdirSync(root)
    .filter((name) => name.endsWith(".json"))
    .map((name) => {
      try {
        return normalizeCollection(
          JSON.parse(fs.readFileSync(path.join(root, name), "utf8"))
        );
      } catch {
        return null;
      }
    })
    .filter((collection): collection is ResearchCollection => Boolean(collection))
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at));
}

export async function getResearchCollection(id: string): Promise<ResearchCollection | null> {
  const target = collectionPath(id);
  if (!fs.existsSync(target)) return null;
  return normalizeCollection(JSON.parse(fs.readFileSync(target, "utf8")));
}

export async function createResearchCollection(input: {
  title?: unknown;
  description?: unknown;
  decision_ids?: unknown;
  notes?: unknown;
}): Promise<ResearchCollection> {
  if (!Array.isArray(input.decision_ids)) {
    throw new Error("decision_ids must be an array");
  }
  const decisionIds = input.decision_ids.filter(
    (item): item is string => typeof item === "string" && item.trim().length > 0
  );
  if (decisionIds.length === 0) {
    throw new Error("select at least one decision");
  }

  const options = await listResearchDecisionOptions();
  const optionById = new Map(options.map((option) => [option.id, option]));
  const optionByExternalRef = new Map(options.map((option) => [option.external_ref, option]));
  const selected = decisionIds
    .map((id) => optionById.get(id) || optionByExternalRef.get(id))
    .filter((option): option is ResearchDecisionOption => Boolean(option));
  if (selected.length !== decisionIds.length) {
    throw new Error("one or more decisions were not found");
  }
  if (selected.some((option) => !isSyntheticExternalRef(option.external_ref))) {
    throw new Error("file-backed demo collections only accept synthetic decisions");
  }

  const now = new Date().toISOString();
  const title =
    typeof input.title === "string" && input.title.trim()
      ? input.title.trim()
      : "Synthetic research collection";
  const id = `${slugify(title)}-${randomUUID().slice(0, 8)}`;
  const collection: ResearchCollection = {
    id,
    title,
    description:
      typeof input.description === "string" ? input.description.trim() : "",
    decision_ids: [...new Set(selected.map((option) => option.id))],
    created_at: now,
    updated_at: now,
    notes: typeof input.notes === "string" ? input.notes.trim() : undefined,
    synthetic_only: true,
  };
  const root = collectionRoot();
  fs.mkdirSync(root, { recursive: true });
  fs.writeFileSync(collectionPath(id), JSON.stringify(collection, null, 2), "utf8");
  return collection;
}

export async function buildResearchCollectionExport(
  id: string
): Promise<ResearchCollectionExport | null> {
  const collection = await getResearchCollection(id);
  if (!collection) return null;
  const selected = await getResearchDecisionSummaries(collection.decision_ids);
  const propositions = await listResearchPropositions(collection.decision_ids);
  const warning =
    "INTERNAL USE ONLY - Synthetic demo research export. Primary sources remain authoritative. Not legal advice.";

  const markdown = [
    `# ${collection.title}`,
    "",
    `> ${warning}`,
    "",
    collection.description,
    "",
    `Decision count: ${selected.length}`,
    "",
    ...selected.flatMap((decision) => [
      `## ${decision.title || decision.external_ref}`,
      "",
      `- Regulator: ${decision.regulator_code}`,
      `- External ref: ${decision.external_ref}`,
      `- Issues: ${decision.issue_categories.join(", ") || "none"}`,
      `- Findings: ${decision.finding_outcomes.join(", ") || "none"}`,
      `- Sanctions: ${decision.sanction_categories.join(", ") || "none"}`,
      "",
      `Summary: ${decision.summary}`,
      "",
      `Takeaway: ${decision.takeaway}`,
      "",
    ]),
  ].join("\n");

  const csvRows = [
    [warning],
    [],
    [
      "collection_id",
      "decision_id",
      "external_ref",
      "regulator_code",
      "prop_type",
      "review_status",
      "claim_text",
    ],
    ...propositions.map((prop) => [
      collection.id,
      prop.decision_id,
      prop.external_ref,
      prop.regulator_code,
      prop.prop_type,
      prop.review_status || "",
      prop.claim_text,
    ]),
  ];

  return {
    collection,
    markdown,
    csv: csvRows.map((row) => row.map(csvEscape).join(",")).join("\n"),
  };
}
