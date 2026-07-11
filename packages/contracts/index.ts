/**
 * Shared RegLens HK contracts (Milestone 2A).
 * Keep in sync with packages/contracts/contracts.v1.json and Python enums.
 */

export const REGULATOR_CODES = ["MCHK", "DCHK"] as const;
export type RegulatorCode = (typeof REGULATOR_CODES)[number];

export const PROFESSIONS = ["doctor", "dentist"] as const;
export type Profession = (typeof PROFESSIONS)[number];

export const PROP_TYPES = [
  "charge",
  "rule",
  "finding",
  "legal_test",
  "aggravating_factor",
  "mitigating_factor",
  "sanction",
  "costs",
  "authority",
  "appeal_status",
] as const;
export type PropType = (typeof PROP_TYPES)[number];

export const EPISTEMIC_CLASSES = ["fact", "interpretation"] as const;
export type EpistemicClass = (typeof EPISTEMIC_CLASSES)[number];

export const REVIEW_STATUSES = [
  "pending",
  "accepted",
  "edited",
  "rejected",
] as const;
export type ReviewStatus = (typeof REVIEW_STATUSES)[number];

export type EvidenceRef = {
  span_id: string | null;
  page_no: number;
  quote: string;
  char_start?: number | null;
  char_end?: number | null;
};

export type Proposition = {
  id: string;
  prop_type: PropType;
  epistemic_class: EpistemicClass;
  claim_text: string;
  confidence: number;
  review_status: ReviewStatus;
  published: boolean;
  evidence: EvidenceRef[];
};

export type DecisionPage = {
  span_id: string;
  page_no: number;
  text: string;
};

export type DecisionRecord = {
  id: string;
  document_id: string;
  document_sha256: string;
  regulator_code: RegulatorCode;
  source_id: string;
  title: string;
  case_ref?: string | null;
  decision_date?: string | null;
  profession?: Profession | null;
  defendant_name_as_published?: string | null;
  defendant_registration_no?: string | null;
  source_url?: string | null;
  licence_notice?: string;
  coverage?: { missing_fields?: string[]; warnings?: string[] };
  text_quality?: string;
  extractor?: Record<string, string>;
  pages: DecisionPage[];
  propositions: Proposition[];
  generated_at?: string;
};

/** Publication is allowed only for reviewed propositions with evidence. */
export function canPublishProposition(p: {
  review_status: ReviewStatus;
  evidence: EvidenceRef[];
}): boolean {
  if (p.review_status !== "accepted" && p.review_status !== "edited") {
    return false;
  }
  return Array.isArray(p.evidence) && p.evidence.length > 0;
}
