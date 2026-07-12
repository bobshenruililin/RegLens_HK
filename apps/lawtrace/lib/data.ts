import { readFileSync, existsSync } from "fs";
import path from "path";

const DATA_ROOT = path.join(process.cwd(), "public", "data");

export type RootManifest = {
  schema_version: string;
  dataset_mode: string;
  product_promise: string;
  disclaimer: string;
  instruments: InstrumentCard[];
};

export type InstrumentCard = {
  instrument_id: string;
  slug: string;
  title: string;
  available: boolean;
  dataset_mode: string;
  missing_reason?: string;
  sampling?: {
    complete: boolean;
    total_available_versions: number;
    versions_included: number;
    strategy: string;
  };
  version_count?: number;
  section_count?: number;
  path: string;
  example_comparison?: {
    instrument_id: string;
    transition_id: string;
    section_id: string;
    from_version: string;
    to_version: string;
    relationship: string;
    heading?: string;
  };
};

function readJson<T>(rel: string): T {
  const full = path.join(DATA_ROOT, rel);
  if (!existsSync(full)) {
    throw new Error(
      `Missing LawTrace data artifact: ${rel}. Run make lawtrace-web-data (or lawtrace-web-data-local).`,
    );
  }
  return JSON.parse(readFileSync(full, "utf8")) as T;
}

export function loadRootManifest(): RootManifest {
  return readJson<RootManifest>("manifest.json");
}

export function loadInstrumentManifest(slug: string) {
  return readJson<Record<string, unknown>>(`instruments/${slug}/manifest.json`);
}

export function loadVersions(slug: string) {
  return readJson<{ versions: Array<Record<string, unknown>> }>(
    `instruments/${slug}/versions.json`,
  );
}

export function loadSections(slug: string) {
  return readJson<{ sections: Array<Record<string, unknown>> }>(
    `instruments/${slug}/sections.json`,
  );
}

export function loadTransitionsIndex(slug: string) {
  return readJson<{ transitions: Array<Record<string, unknown>> }>(
    `instruments/${slug}/transitions.json`,
  );
}

export function loadTransition(slug: string, transitionId: string) {
  return readJson<Record<string, unknown>>(
    `instruments/${slug}/transitions/${transitionId}.json`,
  );
}

export function loadInsights(slug: string) {
  return readJson<Record<string, unknown>>(`instruments/${slug}/insights.json`);
}

export function loadSectionDetail(slug: string, sectionId: string) {
  const safe = sectionId.replace(/[^A-Za-z0-9._-]+/g, "_");
  return readJson<Record<string, unknown>>(
    `instruments/${slug}/sections/${safe}.json`,
  );
}

export function loadMethodology() {
  return readJson<Record<string, unknown>>("methodology.json");
}

/** Local review workspace is opt-in at build time — not authentication. */
export function reviewEnabled(): boolean {
  return process.env.LAWTRACE_LOCAL_REVIEW === "1";
}
