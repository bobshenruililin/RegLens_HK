import fs from "fs";
import path from "path";

/** Public URL prefix for assets under basePath (Pages may use /RegLens_HK). */
export function getBasePath(): string {
  return process.env.NEXT_PUBLIC_BASE_PATH || "";
}

export function withBasePath(href: string): string {
  const base = getBasePath();
  if (!href.startsWith("/")) return href;
  if (!base) return href;
  return `${base}${href}`;
}

export type ReleaseKind = "synthetic_demo" | "public";

export type ReleaseMeta = {
  release_id: string;
  schema_version: string;
  release_mode: ReleaseKind | string;
  generated_at: string;
  released_at?: string;
  title: string;
  description: string;
  decision_count: number;
  proposition_count: number;
  regulators: string[] | Record<string, unknown>;
  methodology_version?: string;
  taxonomy_version?: string;
  global_caveats?: string[];
  source_cutoff_date?: string | null;
  files?: Array<{ path: string; sha256: string; kind?: string }>;
  // Compatibility aliases used by older UI helpers
  version?: string;
  kind?: string;
};

export type CatalogDecision = {
  slug: string;
  public_id: string;
  title: string;
  regulator_code: string;
  profession: string | null;
  year: number | string | null;
  case_refs: string[];
  issue_categories: string[];
  finding_outcomes: string[];
  sanction_categories: string[];
  factor_categories?: string[];
  summary?: string | null;
  official_source_url?: string | null;
  release_mode?: string;
  // Normalized aliases for UI helpers
  id?: string;
  case_ref?: string | null;
  decision_date?: string | null;
  issues?: string[];
  sanctions?: string[];
  source_url?: string | null;
};

export type Catalog = {
  decision_count: number;
  decisions: CatalogDecision[];
  release_id?: string;
  release_mode?: string;
  version?: string;
  kind?: string;
};

export type YearCount = { year: number | string; count: number };
export type RegulatorCount = { regulator: string; count: number };
export type SanctionCount = { sanction: string; count: number };
export type IssueSanctionCount = {
  issue: string;
  sanction: string;
  count: number;
};

export type Analytics = {
  release_id: string;
  release_mode: string;
  schema_version: string;
  decision_count: number;
  proposition_count: number;
  bias_warning: string;
  by_year: Record<string, number> | YearCount[];
  by_regulator: Record<string, number> | RegulatorCount[];
  by_sanction_category?: Record<string, number>;
  by_issue_category?: Record<string, number>;
  by_finding_outcome?: Record<string, number>;
  issue_sanction_heatmap?: Array<{
    issue_category: string;
    sanction_category: string;
    count: number;
  }>;
  // Normalized
  year_rows?: YearCount[];
  regulator_rows?: RegulatorCount[];
  sanction_rows?: SanctionCount[];
  heatmap_rows?: IssueSanctionCount[];
};

export type PublicEvidence = {
  page_no: number;
  excerpt: string;
};

export type PublicProposition = {
  client_ref: string;
  prop_type: string;
  epistemic_class: string;
  derivation?: string;
  claim_text: string;
  verification_status: string;
  evidence: PublicEvidence[];
  structured?: Record<string, unknown> | null;
};

export type PublicDecision = {
  slug: string;
  public_id: string;
  title: string;
  regulator_code: string;
  profession: string | null;
  case_refs: string[];
  dates: Record<string, string | null>;
  official_source_url: string | null;
  source_attribution?: string;
  publication_policy_caveats?: string[];
  editorial_takeaway?: {
    summary: string;
    takeaway: string;
    status: string;
  };
  issue_categories: string[];
  finding_outcomes: string[];
  sanction_categories: string[];
  factor_categories?: string[];
  propositions: PublicProposition[];
  relations?: Array<{
    relation_type: string;
    from_ref: string;
    to_ref: string;
  }>;
  coverage_warnings?: string[];
  release_mode?: string;
  fixture_kind?: string;
};

const RELEASE_DIR = path.join(process.cwd(), "public", "data", "release");

function readJsonFile<T>(filename: string): T {
  const full = path.join(RELEASE_DIR, filename);
  const raw = fs.readFileSync(full, "utf8");
  return JSON.parse(raw) as T;
}

function asRecordCounts(
  value: Record<string, number> | YearCount[] | RegulatorCount[] | undefined,
  keyName: "year" | "regulator" | "sanction",
): Array<{ label: string; count: number }> {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.map((row) => {
      const r = row as Record<string, unknown>;
      return {
        label: String(r[keyName] ?? r.label ?? ""),
        count: Number(r.count ?? 0),
      };
    });
  }
  return Object.entries(value).map(([label, count]) => ({
    label,
    count: Number(count),
  }));
}

export function normalizeRelease(raw: ReleaseMeta): ReleaseMeta {
  return {
    ...raw,
    version: raw.release_id,
    kind: raw.release_mode,
    regulators: Array.isArray(raw.regulators)
      ? raw.regulators
      : Object.keys(raw.regulators || {}),
  };
}

export function normalizeCatalogDecision(d: CatalogDecision): CatalogDecision {
  const caseRef = d.case_ref ?? (d.case_refs && d.case_refs[0]) ?? null;
  const year =
    d.year ??
    (typeof d.decision_date === "string" ? d.decision_date.slice(0, 4) : null);
  return {
    ...d,
    id: d.public_id || d.id || d.slug,
    case_ref: caseRef,
    decision_date: d.decision_date ?? (year ? String(year) : null),
    year,
    issues: d.issues ?? d.issue_categories ?? [],
    sanctions: d.sanctions ?? d.sanction_categories ?? [],
    source_url: d.source_url ?? d.official_source_url ?? null,
  };
}

export function normalizeCatalog(raw: Catalog): Catalog {
  return {
    ...raw,
    version: raw.release_id || raw.version,
    kind: raw.release_mode || raw.kind,
    decisions: (raw.decisions || []).map(normalizeCatalogDecision),
  };
}

export function normalizeAnalytics(raw: Analytics): Analytics {
  const year_rows = asRecordCounts(raw.by_year, "year").map((r) => ({
    year: r.label,
    count: r.count,
  }));
  const regulator_rows = asRecordCounts(raw.by_regulator, "regulator").map(
    (r) => ({ regulator: r.label, count: r.count }),
  );
  const sanction_rows = asRecordCounts(
    raw.by_sanction_category || {},
    "sanction",
  ).map((r) => ({ sanction: r.label, count: r.count }));
  const heatmap_rows = (raw.issue_sanction_heatmap || []).map((c) => ({
    issue: c.issue_category,
    sanction: c.sanction_category,
    count: c.count,
  }));
  return {
    ...raw,
    year_rows,
    regulator_rows,
    sanction_rows,
    heatmap_rows,
  };
}

/** Build-time / server-component loader for release metadata. */
export function loadRelease(): ReleaseMeta {
  return normalizeRelease(readJsonFile<ReleaseMeta>("release.json"));
}

/** Build-time / server-component loader for the decision catalog. */
export function loadCatalog(): Catalog {
  return normalizeCatalog(readJsonFile<Catalog>("catalog.json"));
}

/** Build-time / server-component loader for analytics aggregates. */
export function loadAnalytics(): Analytics {
  return normalizeAnalytics(readJsonFile<Analytics>("analytics.json"));
}

export function loadPublicDecision(slug: string): PublicDecision | null {
  const full = path.join(RELEASE_DIR, "decisions", `${slug}.json`);
  if (!fs.existsSync(full)) return null;
  return JSON.parse(fs.readFileSync(full, "utf8")) as PublicDecision;
}

/** Build-time loader for checksums text. */
export function loadChecksums(): string {
  return fs.readFileSync(path.join(RELEASE_DIR, "checksums.sha256"), "utf8");
}

export function getDecisionBySlug(
  catalog: Catalog,
  slug: string,
): CatalogDecision | undefined {
  return catalog.decisions.find((d) => d.slug === slug);
}

/** Client-side fetch helpers (relative to site basePath). */
export async function fetchCatalog(): Promise<Catalog> {
  const res = await fetch(withBasePath("/data/release/catalog.json"));
  if (!res.ok) throw new Error(`Failed to load catalog (${res.status})`);
  return normalizeCatalog((await res.json()) as Catalog);
}

export async function fetchAnalytics(): Promise<Analytics> {
  const res = await fetch(withBasePath("/data/release/analytics.json"));
  if (!res.ok) throw new Error(`Failed to load analytics (${res.status})`);
  return normalizeAnalytics((await res.json()) as Analytics);
}

export async function fetchRelease(): Promise<ReleaseMeta> {
  const res = await fetch(withBasePath("/data/release/release.json"));
  if (!res.ok) throw new Error(`Failed to load release (${res.status})`);
  return normalizeRelease((await res.json()) as ReleaseMeta);
}

export function isSyntheticKind(kind: string | undefined): boolean {
  return (kind || "").toLowerCase().includes("synthetic");
}

/** Keyword + structured-field match (substring). Not FTS or semantic. */
export function matchesDecision(
  d: CatalogDecision,
  opts: {
    q?: string;
    regulator?: string;
    profession?: string;
    issue?: string;
    sanction?: string;
    year?: string;
    finding?: string;
    rule?: string;
  },
): boolean {
  const nd = normalizeCatalogDecision(d);
  if (opts.regulator && nd.regulator_code !== opts.regulator) return false;
  if (opts.profession && nd.profession !== opts.profession) return false;
  if (opts.issue && !(nd.issues || []).includes(opts.issue)) return false;
  if (opts.sanction && !(nd.sanctions || []).includes(opts.sanction)) {
    return false;
  }
  if (
    opts.finding &&
    !(nd.finding_outcomes || []).includes(opts.finding)
  ) {
    return false;
  }
  if (opts.year) {
    const y = String(nd.year ?? (nd.decision_date || "").slice(0, 4) ?? "");
    if (y !== opts.year) return false;
  }
  const q = (opts.q || "").trim().toLowerCase();
  if (!q) return true;
  const tokens = q.split(/\s+/).filter(Boolean);
  const hay = [
    nd.title,
    nd.case_ref,
    ...(nd.case_refs || []),
    nd.summary,
    nd.regulator_code,
    nd.profession,
    ...(nd.issues || []),
    ...(nd.sanctions || []),
    ...(nd.finding_outcomes || []),
    ...(nd.factor_categories || []),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return tokens.every((t) => hay.includes(t));
}

export function exploreHref(params: Record<string, string | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v) sp.set(k, v);
  }
  const qs = sp.toString();
  return qs ? `/explore/?${qs}` : "/explore/";
}
