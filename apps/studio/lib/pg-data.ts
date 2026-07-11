/**
 * Postgres read/write helpers for Studio (REGLENS_MODE=postgres).
 * Demo mode continues to use lib/data.ts (file seed).
 */

import { query, withTransaction } from "./db";

export type DashboardCounts = {
  decisions: number;
  documents: number;
  jobsPending: number;
  jobsRunning: number;
  reviewsPending: number;
  releases: number;
  auditEvents: number;
};

export async function getDashboardCounts(): Promise<DashboardCounts> {
  const { rows } = await query<{
    decisions: string;
    documents: string;
    jobs_pending: string;
    jobs_running: string;
    reviews_pending: string;
    releases: string;
    audit_events: string;
  }>(
    `
    SELECT
      (SELECT COUNT(*)::text FROM decisions) AS decisions,
      (SELECT COUNT(*)::text FROM documents) AS documents,
      (SELECT COUNT(*)::text FROM jobs WHERE status = 'pending') AS jobs_pending,
      (SELECT COUNT(*)::text FROM jobs WHERE status = 'running') AS jobs_running,
      (SELECT COUNT(*)::text FROM reviews WHERE review_status = 'pending') AS reviews_pending,
      (SELECT COUNT(*)::text FROM publication_releases) AS releases,
      (SELECT COUNT(*)::text FROM audit_events) AS audit_events
    `
  );
  const r = rows[0];
  return {
    decisions: Number(r?.decisions || 0),
    documents: Number(r?.documents || 0),
    jobsPending: Number(r?.jobs_pending || 0),
    jobsRunning: Number(r?.jobs_running || 0),
    reviewsPending: Number(r?.reviews_pending || 0),
    releases: Number(r?.releases || 0),
    auditEvents: Number(r?.audit_events || 0),
  };
}

export type JobRow = {
  id: string;
  job_type: string;
  dedupe_key: string;
  status: string;
  attempts: number;
  max_attempts: number;
  last_error: string | null;
  available_at: Date;
  created_at: Date;
  updated_at: Date;
  started_at: Date | null;
  finished_at: Date | null;
};

export async function listJobs(limit = 100): Promise<JobRow[]> {
  const { rows } = await query<JobRow>(
    `
    SELECT id, job_type, dedupe_key, status, attempts, max_attempts,
           last_error, available_at, created_at, updated_at, started_at, finished_at
    FROM jobs
    ORDER BY created_at DESC
    LIMIT $1
    `,
    [limit]
  );
  return rows;
}

export type DocumentListItem = {
  id: string;
  external_ref: string;
  title: string | null;
  language: string;
  ingest_status: string;
  source_id: string;
  regulator_code: string;
  created_at: Date;
};

export async function listDocuments(limit = 100): Promise<DocumentListItem[]> {
  const { rows } = await query<DocumentListItem>(
    `
    SELECT d.id, d.external_ref, d.title, d.language, d.ingest_status,
           sc.source_id, r.code AS regulator_code, d.created_at
    FROM documents d
    JOIN source_collections sc ON sc.id = d.source_collection_id
    JOIN regulators r ON r.id = sc.regulator_id
    ORDER BY d.created_at DESC
    LIMIT $1
    `,
    [limit]
  );
  return rows;
}

export type DocumentDetail = DocumentListItem & {
  versions: Array<{
    id: string;
    version_number: number;
    sha256: string;
    storage_key: string;
    acquired_at: Date;
  }>;
};

export async function getDocument(id: string): Promise<DocumentDetail | null> {
  const { rows } = await query<DocumentListItem>(
    `
    SELECT d.id, d.external_ref, d.title, d.language, d.ingest_status,
           sc.source_id, r.code AS regulator_code, d.created_at
    FROM documents d
    JOIN source_collections sc ON sc.id = d.source_collection_id
    JOIN regulators r ON r.id = sc.regulator_id
    WHERE d.id = $1
    `,
    [id]
  );
  const doc = rows[0];
  if (!doc) return null;
  const versions = await query<{
    id: string;
    version_number: number;
    sha256: string;
    storage_key: string;
    acquired_at: Date;
  }>(
    `
    SELECT id, version_number, sha256, storage_key, acquired_at
    FROM document_versions
    WHERE document_id = $1
    ORDER BY version_number
    `,
    [id]
  );
  return { ...doc, versions: versions.rows };
}

export type DecisionListItem = {
  id: string;
  external_ref: string;
  title: string | null;
  profession: string;
  fixture_kind: string;
  regulator_code: string;
  source_id: string;
  created_at: Date;
};

export async function listDecisionsPg(limit = 100): Promise<DecisionListItem[]> {
  const { rows } = await query<DecisionListItem>(
    `
    SELECT d.id, d.external_ref, d.title, d.profession, d.fixture_kind,
           r.code AS regulator_code, sc.source_id, d.created_at
    FROM decisions d
    JOIN regulators r ON r.id = d.regulator_id
    JOIN source_collections sc ON sc.id = d.source_collection_id
    ORDER BY d.created_at DESC
    LIMIT $1
    `,
    [limit]
  );
  return rows;
}

export type ReviewQueueItem = {
  review_id: string;
  decision_id: string;
  decision_title: string | null;
  external_ref: string;
  regulator_code: string;
  proposition_revision_id: string;
  extracted_proposition_id: string;
  revision_number: number;
  claim_text: string;
  prop_type: string;
  epistemic_class: string;
  client_ref: string;
  evidence: Array<{ page_no: number; quote_text: string }>;
};

export async function listPendingReviews(limit = 100): Promise<ReviewQueueItem[]> {
  const { rows } = await query<Omit<ReviewQueueItem, "evidence">>(
    `
    SELECT
      rv.id AS review_id,
      rv.decision_id,
      d.title AS decision_title,
      d.external_ref,
      r.code AS regulator_code,
      rv.proposition_revision_id,
      rv.extracted_proposition_id,
      pr.revision_number,
      pr.claim_text,
      pr.prop_type,
      pr.epistemic_class,
      ep.client_ref
    FROM reviews rv
    JOIN proposition_revisions pr ON pr.id = rv.proposition_revision_id
    JOIN extracted_propositions ep ON ep.id = rv.extracted_proposition_id
    JOIN decisions d ON d.id = rv.decision_id
    JOIN regulators r ON r.id = d.regulator_id
    WHERE rv.review_status = 'pending'
    ORDER BY rv.created_at ASC
    LIMIT $1
    `,
    [limit]
  );

  const out: ReviewQueueItem[] = [];
  for (const row of rows) {
    const ev = await query<{ page_no: number; quote_text: string }>(
      `
      SELECT page_no, quote_text
      FROM proposition_evidence
      WHERE extracted_proposition_id = $1
      ORDER BY page_no
      `,
      [row.extracted_proposition_id]
    );
    out.push({ ...row, evidence: ev.rows });
  }
  return out;
}

export type DecisionReviewBundle = {
  decision: {
    id: string;
    external_ref: string;
    title: string | null;
    profession: string;
    regulator_code: string;
    defendant_name_as_published: string | null;
  };
  spans: Array<{
    id: string;
    page_no: number;
    text: string;
    stable_span_id: string;
  }>;
  propositions: Array<{
    extracted_proposition_id: string;
    client_ref: string;
    prop_type: string;
    epistemic_class: string;
    claim_text: string;
    revision_id: string;
    revision_number: number;
    latest_review_status: string | null;
    evidence: Array<{ page_no: number; quote_text: string }>;
  }>;
};

export async function getDecisionReviewBundle(
  decisionId: string
): Promise<DecisionReviewBundle | null> {
  const { rows } = await query<{
    id: string;
    external_ref: string;
    title: string | null;
    profession: string;
    regulator_code: string;
    defendant_name_as_published: string | null;
  }>(
    `
    SELECT d.id, d.external_ref, d.title, d.profession,
           r.code AS regulator_code, d.defendant_name_as_published
    FROM decisions d
    JOIN regulators r ON r.id = d.regulator_id
    WHERE d.id = $1
    `,
    [decisionId]
  );
  const decision = rows[0];
  if (!decision) return null;

  const spans = await query<{
    id: string;
    page_no: number;
    text: string;
    stable_span_id: string;
  }>(
    `
    SELECT ds.id, ds.page_no, ds.text, ds.stable_span_id
    FROM document_spans ds
    JOIN document_versions dv ON dv.id = ds.document_version_id
    JOIN decision_document_versions ddv ON ddv.document_version_id = dv.id
    WHERE ddv.decision_id = $1
    ORDER BY ds.page_no, ds.stable_span_id
    `,
    [decisionId]
  );

  const props = await query<{
    extracted_proposition_id: string;
    client_ref: string;
    prop_type: string;
    epistemic_class: string;
    claim_text: string;
    revision_id: string;
    revision_number: number;
    latest_review_status: string | null;
  }>(
    `
    SELECT DISTINCT ON (pr.extracted_proposition_id)
      pr.extracted_proposition_id,
      ep.client_ref,
      pr.prop_type,
      pr.epistemic_class,
      pr.claim_text,
      pr.id AS revision_id,
      pr.revision_number,
      (
        SELECT rv.review_status
        FROM reviews rv
        WHERE rv.proposition_revision_id = pr.id
        ORDER BY rv.created_at DESC
        LIMIT 1
      ) AS latest_review_status
    FROM proposition_revisions pr
    JOIN extracted_propositions ep ON ep.id = pr.extracted_proposition_id
    WHERE pr.decision_id = $1
    ORDER BY pr.extracted_proposition_id, pr.revision_number DESC
    `,
    [decisionId]
  );

  const propositions = [];
  for (const p of props.rows) {
    const ev = await query<{ page_no: number; quote_text: string }>(
      `
      SELECT page_no, quote_text
      FROM proposition_evidence
      WHERE extracted_proposition_id = $1
      ORDER BY page_no
      `,
      [p.extracted_proposition_id]
    );
    propositions.push({ ...p, evidence: ev.rows });
  }

  return {
    decision,
    spans: spans.rows,
    propositions,
  };
}

export async function submitReviewAction(opts: {
  extractedPropositionId: string;
  reviewerUserId: string;
  reviewStatus: "accepted" | "edited" | "rejected";
  claimText?: string | null;
  expectedHeadRevisionNumber: number;
  notes?: string | null;
}): Promise<{ revisionId: string; reviewId: string; status: string }> {
  return withTransaction(async (client) => {
    const headRes = await client.query<{
      id: string;
      decision_id: string;
      revision_number: number;
      claim_text: string;
      prop_type: string;
      epistemic_class: string;
      derivation: string;
      structured_json: unknown;
    }>(
      `
      SELECT *
      FROM proposition_revisions
      WHERE extracted_proposition_id = $1
      ORDER BY revision_number DESC
      LIMIT 1
      FOR UPDATE
      `,
      [opts.extractedPropositionId]
    );
    const head = headRes.rows[0];
    if (!head) throw new Error("No revisions for proposition");
    if (Number(head.revision_number) !== Number(opts.expectedHeadRevisionNumber)) {
      throw new Error(
        `Revision conflict: expected=${opts.expectedHeadRevisionNumber}, actual=${head.revision_number}`
      );
    }

    let revisionId = head.id;
    let status = opts.reviewStatus;

    if (
      opts.claimText != null &&
      opts.claimText !== head.claim_text &&
      opts.reviewStatus !== "rejected"
    ) {
      const nextNum = Number(head.revision_number) + 1;
      const ins = await client.query<{ id: string }>(
        `
        INSERT INTO proposition_revisions (
          extracted_proposition_id, decision_id, revision_number,
          supersedes_revision_id, origin, prop_type, epistemic_class,
          derivation, claim_text, structured_json, created_by_user_id
        ) VALUES ($1, $2, $3, $4, 'human_edited', $5, $6, $7, $8, $9, $10)
        RETURNING id
        `,
        [
          opts.extractedPropositionId,
          head.decision_id,
          nextNum,
          head.id,
          head.prop_type,
          head.epistemic_class,
          head.derivation,
          opts.claimText,
          head.structured_json,
          opts.reviewerUserId,
        ]
      );
      revisionId = ins.rows[0].id;
      status = "edited";
    }

    if (status === "accepted" || status === "edited") {
      const ev = await client.query<{ c: string }>(
        `
        SELECT COUNT(*)::text AS c
        FROM proposition_evidence
        WHERE extracted_proposition_id = $1
        `,
        [opts.extractedPropositionId]
      );
      if (Number(ev.rows[0]?.c || 0) < 1) {
        throw new Error("cannot accept/edit without evidence spans");
      }
    }

    await client.query(
      `
      DELETE FROM reviews
      WHERE proposition_revision_id = $1 AND review_status = 'pending'
      `,
      [revisionId]
    );

    const review = await client.query<{ id: string }>(
      `
      INSERT INTO reviews (
        decision_id, proposition_revision_id, extracted_proposition_id,
        reviewer_user_id, review_status, notes
      ) VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING id
      `,
      [
        head.decision_id,
        revisionId,
        opts.extractedPropositionId,
        opts.reviewerUserId,
        status,
        opts.notes ?? null,
      ]
    );

    return { revisionId, reviewId: review.rows[0].id, status };
  });
}

export type ReleaseListItem = {
  id: string;
  release_id: string;
  release_mode: string;
  status: string;
  version: number;
  title: string;
  decision_count: number;
  created_at: Date;
  updated_at: Date;
};

export async function listReleases(limit = 50): Promise<ReleaseListItem[]> {
  const { rows } = await query<ReleaseListItem>(
    `
    SELECT id, release_id, release_mode, status, version, title,
           decision_count, created_at, updated_at
    FROM publication_releases
    ORDER BY created_at DESC
    LIMIT $1
    `,
    [limit]
  );
  return rows;
}

export type ReleaseDetail = ReleaseListItem & {
  description: string;
  corpus: string;
  methodology_version: string;
  taxonomy_version: string;
  inclusion_criteria: string;
  exclusion_criteria: string;
  items: Array<{
    id: string;
    decision_id: string;
    external_ref: string;
    public_slug: string;
    included: boolean;
    exclusion_reason: string | null;
    decision_title: string | null;
  }>;
};

export async function getRelease(releaseId: string): Promise<ReleaseDetail | null> {
  const { rows } = await query<
    ReleaseListItem & {
      description: string;
      corpus: string;
      methodology_version: string;
      taxonomy_version: string;
      inclusion_criteria: string;
      exclusion_criteria: string;
    }
  >(
    `
    SELECT id, release_id, release_mode, status, version, title, description,
           corpus, methodology_version, taxonomy_version,
           inclusion_criteria, exclusion_criteria,
           decision_count, created_at, updated_at
    FROM publication_releases
    WHERE release_id = $1 OR id::text = $1
    `,
    [releaseId]
  );
  const release = rows[0];
  if (!release) return null;
  const items = await query<{
    id: string;
    decision_id: string;
    external_ref: string;
    public_slug: string;
    included: boolean;
    exclusion_reason: string | null;
    decision_title: string | null;
  }>(
    `
    SELECT i.id, i.decision_id, i.external_ref, i.public_slug, i.included,
           i.exclusion_reason, d.title AS decision_title
    FROM publication_release_items i
    JOIN decisions d ON d.id = i.decision_id
    WHERE i.publication_release_id = $1
    ORDER BY i.public_slug
    `,
    [release.id]
  );
  return { ...release, items: items.rows };
}

const PUBLISHABLE = new Set(["accepted", "edited"]);

/**
 * Fail-closed validate + approve (status → ready), mirroring Python
 * approve_and_build_release core checks (accepted revisions + evidence).
 */
export async function approveRelease(opts: {
  publicationReleaseId: string;
  expectedVersion: number;
  actorUserId: string;
}): Promise<{ status: string; version: number; errors?: string[] }> {
  return withTransaction(async (client) => {
    const lock = await client.query<{
      id: string;
      status: string;
      version: number;
      release_mode: string;
    }>(
      `
      SELECT id, status, version, release_mode
      FROM publication_releases
      WHERE id = $1
      FOR UPDATE
      `,
      [opts.publicationReleaseId]
    );
    const release = lock.rows[0];
    if (!release) throw new Error("Unknown publication_release");
    if (Number(release.version) !== Number(opts.expectedVersion)) {
      throw new Error(
        `Version conflict: expected=${opts.expectedVersion}, actual=${release.version}`
      );
    }
    if (!["draft", "ready", "failed"].includes(release.status)) {
      throw new Error(`Cannot approve release in status=${release.status}`);
    }

    const errors: string[] = [];
    const items = await client.query<{
      decision_id: string;
      external_ref: string;
      fixture_kind: string;
      visibility: string;
      source_id: string;
      official_source_url: string | null;
    }>(
      `
      SELECT i.decision_id, i.external_ref, d.fixture_kind, sc.visibility,
             sc.source_id, d.official_source_url
      FROM publication_release_items i
      JOIN decisions d ON d.id = i.decision_id
      JOIN source_collections sc ON sc.id = d.source_collection_id
      WHERE i.publication_release_id = $1 AND i.included = TRUE
      `,
      [opts.publicationReleaseId]
    );
    if (items.rows.length === 0) {
      errors.push("Release has no included decisions");
    }

    const kinds = new Set<string>();
    for (const item of items.rows) {
      kinds.add(item.fixture_kind);
      if (release.release_mode === "synthetic_demo" && item.fixture_kind !== "synthetic") {
        errors.push(
          `synthetic_demo refuses non-synthetic decision ${item.decision_id}`
        );
      }
      if (release.release_mode === "public") {
        if (item.fixture_kind === "synthetic") {
          errors.push(`public release refuses synthetic decision ${item.decision_id}`);
        }
        if (item.visibility === "internal_only") {
          errors.push(
            `Source ${item.source_id} is internal_only; cannot include ${item.decision_id}`
          );
        }
        if (!item.official_source_url) {
          errors.push(
            `Real public decision ${item.external_ref} requires official_source_url`
          );
        }
      }

      const heads = await client.query<{
        id: string;
        client_ref: string;
        latest_review_status: string | null;
        evidence_count: number;
      }>(
        `
        SELECT DISTINCT ON (pr.extracted_proposition_id)
          pr.id,
          ep.client_ref,
          (
            SELECT rv.review_status FROM reviews rv
            WHERE rv.proposition_revision_id = pr.id
            ORDER BY rv.created_at DESC LIMIT 1
          ) AS latest_review_status,
          (
            SELECT COUNT(*)::int FROM proposition_evidence pe
            WHERE pe.extracted_proposition_id = pr.extracted_proposition_id
          ) AS evidence_count
        FROM proposition_revisions pr
        JOIN extracted_propositions ep ON ep.id = pr.extracted_proposition_id
        WHERE pr.decision_id = $1
        ORDER BY pr.extracted_proposition_id, pr.revision_number DESC
        `,
        [item.decision_id]
      );
      if (heads.rows.length === 0) {
        errors.push(`Decision ${item.decision_id} has no proposition revisions`);
        continue;
      }
      let publishable = 0;
      for (const rev of heads.rows) {
        if (!PUBLISHABLE.has(rev.latest_review_status || "")) {
          errors.push(
            `Revision ${rev.id} (${rev.client_ref}) not accepted/edited (status=${rev.latest_review_status})`
          );
          continue;
        }
        if (Number(rev.evidence_count) < 1) {
          errors.push(`Revision ${rev.id} (${rev.client_ref}) has no evidence`);
          continue;
        }
        publishable += 1;
      }
      if (publishable < 1) {
        errors.push(
          `Decision ${item.decision_id} has no publishable accepted/edited revisions`
        );
      }

      const ann = await client.query(
        `
        SELECT 1 FROM editorial_annotations
        WHERE decision_id = $1 OR external_ref = $2
        LIMIT 1
        `,
        [item.decision_id, item.external_ref]
      );
      if (ann.rows.length === 0) {
        errors.push(
          `Missing editorial annotation for decision ${item.decision_id} / ${item.external_ref}`
        );
      }
    }
    if (kinds.has("synthetic") && kinds.has("real")) {
      errors.push("Release mixes synthetic and real material");
    }

    if (errors.length) {
      return { status: release.status, version: release.version, errors };
    }

    const updated = await client.query<{ status: string; version: number }>(
      `
      UPDATE publication_releases
      SET status = 'ready',
          version = version + 1,
          updated_at = now(),
          generated_at = COALESCE(generated_at, now())
      WHERE id = $1
      RETURNING status, version
      `,
      [opts.publicationReleaseId]
    );

    await client.query(
      `
      INSERT INTO audit_events (
        actor, actor_user_id, action, entity_type, entity_id, before_json, after_json
      ) VALUES (
        'publisher', $1, 'release.approve', 'publication_release', $2, $3::jsonb, $4::jsonb
      )
      `,
      [
        opts.actorUserId,
        opts.publicationReleaseId,
        JSON.stringify({ status: release.status, version: release.version }),
        JSON.stringify(updated.rows[0]),
      ]
    );

    return {
      status: updated.rows[0].status,
      version: updated.rows[0].version,
    };
  });
}

export type AuditEventRow = {
  id: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string;
  at: Date;
};

export async function listAuditEvents(limit = 100): Promise<AuditEventRow[]> {
  const { rows } = await query<AuditEventRow>(
    `
    SELECT id, actor, action, entity_type, entity_id, at
    FROM audit_events
    ORDER BY at DESC
    LIMIT $1
    `,
    [limit]
  );
  return rows;
}

export type SourcePolicyRow = {
  source_id: string;
  collection_name: string;
  visibility: string;
  consent_status: string;
  max_excerpt_chars: number;
  attribution_required: boolean;
  notes: string | null;
  regulator_code: string;
};

export async function listSourcePoliciesFromDb(): Promise<SourcePolicyRow[]> {
  const { rows } = await query<SourcePolicyRow>(
    `
    SELECT sc.source_id, sc.collection_name, sc.visibility, sc.consent_status,
           sc.max_excerpt_chars, sc.attribution_required, sc.notes,
           r.code AS regulator_code
    FROM source_collections sc
    JOIN regulators r ON r.id = sc.regulator_id
    ORDER BY r.code, sc.source_id
    `
  );
  return rows;
}
