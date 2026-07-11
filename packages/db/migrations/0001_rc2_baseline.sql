-- RegLens HK MVP-RC2 operational schema baseline
-- PostgreSQL 16+
--
-- schema_migrations is owned by the migration runner — do not create it here.
-- No pgvector / embeddings. Studio search uses PostgreSQL FTS only.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------------
-- Shared helpers (check patterns)
-- ---------------------------------------------------------------------------
-- SHA-256 digests are stored as lowercase 64-char hex strings.

-- ===========================================================================
-- Regulators & source collections
-- ===========================================================================

CREATE TABLE regulators (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    homepage_url    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT regulators_code_unique UNIQUE (code),
    CONSTRAINT regulators_code_nonempty CHECK (length(trim(code)) > 0),
    CONSTRAINT regulators_name_nonempty CHECK (length(trim(name)) > 0)
);

COMMENT ON TABLE regulators IS
    'MVP regulators (MCHK, DCHK). NCHK and others are out of scope until audited.';

CREATE TABLE source_collections (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    regulator_id        UUID NOT NULL REFERENCES regulators (id),
    source_id           TEXT NOT NULL,
    collection_name     TEXT NOT NULL,
    index_url           TEXT,
    visibility          TEXT NOT NULL DEFAULT 'internal_only',
    consent_status      TEXT NOT NULL DEFAULT 'not_requested',
    max_excerpt_chars   INTEGER NOT NULL DEFAULT 280
                        CHECK (max_excerpt_chars > 0),
    attribution_required BOOLEAN NOT NULL DEFAULT TRUE,
    terms_reviewed_at   TIMESTAMPTZ,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT source_collections_source_id_unique UNIQUE (source_id),
    CONSTRAINT source_collections_visibility_check CHECK (
        visibility IN (
            'internal_only',
            'public_metadata_only',
            'public_excerpt',
            'public_fulltext'
        )
    ),
    CONSTRAINT source_collections_consent_status_check CHECK (
        consent_status IN (
            'not_requested',
            'requested',
            'granted',
            'refused',
            'withdrawn'
        )
    ),
    CONSTRAINT source_collections_source_id_nonempty CHECK (length(trim(source_id)) > 0)
);

COMMENT ON TABLE source_collections IS
    'Licensed document collections. visibility + consent_status gate publication; '
    'do not flip without a licensing decision.';

CREATE INDEX source_collections_regulator_id_idx
    ON source_collections (regulator_id);

-- ===========================================================================
-- Content-addressed blobs & acquisitions
-- ===========================================================================

CREATE TABLE blobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sha256          TEXT NOT NULL,
    storage_key     TEXT NOT NULL,
    byte_size       BIGINT NOT NULL CHECK (byte_size >= 0),
    mime_type       TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    immutable       BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT blobs_sha256_unique UNIQUE (sha256),
    CONSTRAINT blobs_storage_key_unique UNIQUE (storage_key),
    CONSTRAINT blobs_sha256_hex CHECK (sha256 ~ '^[a-f0-9]{64}$'),
    CONSTRAINT blobs_storage_key_nonempty CHECK (length(trim(storage_key)) > 0),
    CONSTRAINT blobs_mime_type_nonempty CHECK (length(trim(mime_type)) > 0),
    CONSTRAINT blobs_immutable_true CHECK (immutable = TRUE)
);

COMMENT ON TABLE blobs IS
    'Immutable content-addressed object-store metadata. Bytes live under storage_key; '
    'never update blob rows in place — new bytes ⇒ new sha256.';

CREATE TABLE acquisitions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_collection_id    UUID NOT NULL REFERENCES source_collections (id),
    blob_id                 UUID NOT NULL REFERENCES blobs (id),
    external_ref            TEXT NOT NULL,
    source_url              TEXT,
    fixture_kind            TEXT NOT NULL,
    title                   TEXT,
    acquired_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    acquired_by             TEXT,
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT acquisitions_fixture_kind_check CHECK (
        fixture_kind IN ('synthetic', 'real')
    ),
    CONSTRAINT acquisitions_external_ref_nonempty CHECK (length(trim(external_ref)) > 0),
    CONSTRAINT acquisitions_collection_blob_unique UNIQUE (source_collection_id, blob_id),
    CONSTRAINT acquisitions_collection_external_ref_unique
        UNIQUE (source_collection_id, external_ref)
);

COMMENT ON TABLE acquisitions IS
    'Manual acquisition records linking a source collection item to an immutable blob. '
    'No live crawl — fixture_kind marks synthetic vs real private-data rows.';

CREATE INDEX acquisitions_blob_id_idx ON acquisitions (blob_id);
CREATE INDEX acquisitions_external_ref_idx ON acquisitions (external_ref);

-- ===========================================================================
-- Documents & versions
-- ===========================================================================

CREATE TABLE documents (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_collection_id    UUID NOT NULL REFERENCES source_collections (id),
    external_ref            TEXT NOT NULL,
    title                   TEXT,
    language                TEXT NOT NULL DEFAULT 'en',
    ingest_status           TEXT NOT NULL DEFAULT 'stored',
    text_quality            TEXT,
    ocr_used                BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT documents_collection_external_ref_unique
        UNIQUE (source_collection_id, external_ref),
    CONSTRAINT documents_external_ref_nonempty CHECK (length(trim(external_ref)) > 0),
    CONSTRAINT documents_ingest_status_check CHECK (
        ingest_status IN (
            'stored',
            'segmented',
            'extracted',
            'failed',
            'quarantined'
        )
    )
);

COMMENT ON TABLE documents IS
    'Logical document identity within a source collection (stable external_ref). '
    'Byte identity lives on blobs / document_versions.';

CREATE INDEX documents_source_collection_id_idx ON documents (source_collection_id);

CREATE TABLE document_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents (id),
    blob_id         UUID NOT NULL REFERENCES blobs (id),
    version_number  INTEGER NOT NULL CHECK (version_number >= 1),
    sha256          TEXT NOT NULL,
    storage_key     TEXT NOT NULL,
    acquired_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    note            TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT document_versions_document_version_unique UNIQUE (document_id, version_number),
    CONSTRAINT document_versions_document_sha256_unique UNIQUE (document_id, sha256),
    CONSTRAINT document_versions_sha256_hex CHECK (sha256 ~ '^[a-f0-9]{64}$'),
    CONSTRAINT document_versions_storage_key_nonempty CHECK (length(trim(storage_key)) > 0)
);

COMMENT ON TABLE document_versions IS
    'Immutable versions of a logical document. Prefer originals; new bytes get a new version.';

CREATE INDEX document_versions_blob_id_idx ON document_versions (blob_id);
CREATE INDEX document_versions_sha256_idx ON document_versions (sha256);

-- ===========================================================================
-- Decisions & metadata
-- ===========================================================================

CREATE TABLE decisions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    regulator_id            UUID NOT NULL REFERENCES regulators (id),
    source_collection_id    UUID NOT NULL REFERENCES source_collections (id),
    external_ref            TEXT NOT NULL,
    profession              TEXT NOT NULL,
    title                   TEXT,
    defendant_name_as_published TEXT,
    defendant_registration_no   TEXT,
    appeal_status_as_stated TEXT,
    coverage_json           JSONB NOT NULL DEFAULT '{}'::jsonb,
    fixture_kind            TEXT NOT NULL DEFAULT 'synthetic',
    official_source_url     TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT decisions_collection_external_ref_unique
        UNIQUE (source_collection_id, external_ref),
    CONSTRAINT decisions_profession_check CHECK (
        profession IN ('doctor', 'dentist')
    ),
    CONSTRAINT decisions_fixture_kind_check CHECK (
        fixture_kind IN ('synthetic', 'real')
    ),
    CONSTRAINT decisions_external_ref_nonempty CHECK (length(trim(external_ref)) > 0),
    CONSTRAINT decisions_coverage_is_object CHECK (jsonb_typeof(coverage_json) = 'object')
);

COMMENT ON TABLE decisions IS
    'Studio decision aggregate. Public Observatory only sees rows projected through '
    'a trusted publication_releases transaction into publication_release.v1.';

CREATE INDEX decisions_regulator_id_idx ON decisions (regulator_id);
CREATE INDEX decisions_profession_idx ON decisions (profession);
CREATE INDEX decisions_fixture_kind_idx ON decisions (fixture_kind);
CREATE INDEX decisions_external_ref_idx ON decisions (external_ref);

-- Denormalised FTS document for decision browse/search in Studio
ALTER TABLE decisions
    ADD COLUMN search_tsv tsvector
    GENERATED ALWAYS AS (
        to_tsvector(
            'english',
            coalesce(title, '') || ' ' ||
            coalesce(external_ref, '') || ' ' ||
            coalesce(defendant_name_as_published, '') || ' ' ||
            coalesce(appeal_status_as_stated, '')
        )
    ) STORED;

CREATE INDEX decisions_search_tsv_idx ON decisions USING GIN (search_tsv);

CREATE TABLE decision_case_refs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id     UUID NOT NULL REFERENCES decisions (id) ON DELETE CASCADE,
    case_ref        TEXT NOT NULL,
    ordinal         INTEGER NOT NULL DEFAULT 0 CHECK (ordinal >= 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT decision_case_refs_unique UNIQUE (decision_id, case_ref),
    CONSTRAINT decision_case_refs_nonempty CHECK (length(trim(case_ref)) > 0)
);

CREATE INDEX decision_case_refs_case_ref_idx ON decision_case_refs (case_ref);

CREATE TABLE decision_dates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id     UUID NOT NULL REFERENCES decisions (id) ON DELETE CASCADE,
    date_type       TEXT NOT NULL,
    date_value      DATE NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT decision_dates_type_unique UNIQUE (decision_id, date_type),
    CONSTRAINT decision_dates_type_check CHECK (
        date_type IN (
            'inquiry',
            'judgment',
            'publication',
            'conduct',
            'order_effective'
        )
    )
);

CREATE INDEX decision_dates_date_value_idx ON decision_dates (date_value);
CREATE INDEX decision_dates_date_type_idx ON decision_dates (date_type);

CREATE TABLE decision_document_versions (
    decision_id             UUID NOT NULL REFERENCES decisions (id) ON DELETE CASCADE,
    document_version_id     UUID NOT NULL REFERENCES document_versions (id),
    role                    TEXT NOT NULL DEFAULT 'primary',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (decision_id, document_version_id),
    CONSTRAINT decision_document_versions_role_check CHECK (
        role IN ('primary', 'supporting', 'superseded')
    )
);

CREATE UNIQUE INDEX decision_document_versions_one_primary_uidx
    ON decision_document_versions (decision_id)
    WHERE role = 'primary';

CREATE INDEX decision_document_versions_document_version_id_idx
    ON decision_document_versions (document_version_id);

-- ===========================================================================
-- Document spans (provenance units)
-- ===========================================================================

CREATE TABLE document_spans (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id     UUID NOT NULL REFERENCES document_versions (id) ON DELETE CASCADE,
    page_no                 INTEGER NOT NULL CHECK (page_no >= 1),
    span_type               TEXT NOT NULL DEFAULT 'page',
    char_start              INTEGER CHECK (char_start IS NULL OR char_start >= 0),
    char_end                INTEGER CHECK (char_end IS NULL OR char_end >= 0),
    text                    TEXT NOT NULL,
    text_hash               TEXT NOT NULL,
    bbox_json               JSONB,
    stable_span_id          TEXT NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT document_spans_span_type_check CHECK (
        span_type IN ('page', 'block', 'paragraph')
    ),
    CONSTRAINT document_spans_offsets_pair CHECK (
        (char_start IS NULL AND char_end IS NULL)
        OR (char_start IS NOT NULL AND char_end IS NOT NULL AND char_end >= char_start)
    ),
    CONSTRAINT document_spans_text_hash_hex CHECK (text_hash ~ '^[a-f0-9]{64}$'),
    CONSTRAINT document_spans_stable_span_id_nonempty CHECK (length(trim(stable_span_id)) > 0),
    CONSTRAINT document_spans_version_page_type_hash_unique
        UNIQUE (document_version_id, page_no, span_type, text_hash),
    CONSTRAINT document_spans_stable_span_id_unique UNIQUE (stable_span_id)
);

COMMENT ON TABLE document_spans IS
    'Immutable page/block provenance units for a document_version. '
    'Quotes in evidence must align to these spans; never mutate span text for redaction.';

CREATE INDEX document_spans_document_version_id_idx
    ON document_spans (document_version_id);
CREATE INDEX document_spans_page_no_idx
    ON document_spans (document_version_id, page_no);

ALTER TABLE document_spans
    ADD COLUMN text_tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', coalesce(text, ''))) STORED;

CREATE INDEX document_spans_text_tsv_idx ON document_spans USING GIN (text_tsv);

-- ===========================================================================
-- Extraction runs & immutable extracted propositions
-- ===========================================================================

CREATE TABLE extraction_runs (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_key                 TEXT NOT NULL,
    document_version_id     UUID NOT NULL REFERENCES document_versions (id),
    decision_id             UUID REFERENCES decisions (id),
    pipeline_version        TEXT NOT NULL,
    model_provider          TEXT NOT NULL,
    model_version           TEXT NOT NULL,
    prompt_version          TEXT NOT NULL,
    schema_version          TEXT NOT NULL DEFAULT '2.0.0',
    input_hash              TEXT NOT NULL,
    output_sha256           TEXT,
    status                  TEXT NOT NULL DEFAULT 'running',
    coverage_json           JSONB NOT NULL DEFAULT '{"missing_fields":[],"warnings":[]}'::jsonb,
    started_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT extraction_runs_run_key_unique UNIQUE (run_key),
    CONSTRAINT extraction_runs_run_key_hex CHECK (run_key ~ '^[a-f0-9]{64}$'),
    CONSTRAINT extraction_runs_input_hash_hex CHECK (input_hash ~ '^[a-f0-9]{64}$'),
    CONSTRAINT extraction_runs_output_sha256_hex CHECK (
        output_sha256 IS NULL OR output_sha256 ~ '^[a-f0-9]{64}$'
    ),
    CONSTRAINT extraction_runs_status_check CHECK (
        status IN ('running', 'succeeded', 'failed', 'quarantined')
    ),
    CONSTRAINT extraction_runs_versions_nonempty CHECK (
        length(trim(pipeline_version)) > 0
        AND length(trim(model_provider)) > 0
        AND length(trim(model_version)) > 0
        AND length(trim(prompt_version)) > 0
    ),
    CONSTRAINT extraction_runs_doc_input_unique UNIQUE (document_version_id, input_hash)
);

COMMENT ON TABLE extraction_runs IS
    'Immutable extraction run identity (run_key). Conflicting bytes for the same key '
    'must quarantine — see ADR 0002.';

CREATE INDEX extraction_runs_document_version_id_idx
    ON extraction_runs (document_version_id);
CREATE INDEX extraction_runs_decision_id_idx
    ON extraction_runs (decision_id);
CREATE INDEX extraction_runs_status_idx
    ON extraction_runs (status);

CREATE TABLE extracted_propositions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_run_id   UUID NOT NULL REFERENCES extraction_runs (id) ON DELETE CASCADE,
    decision_id         UUID NOT NULL REFERENCES decisions (id),
    client_ref          TEXT NOT NULL,
    prop_type           TEXT NOT NULL,
    epistemic_class     TEXT NOT NULL,
    derivation          TEXT NOT NULL,
    claim_text          TEXT NOT NULL,
    structured_json     JSONB,
    confidence          DOUBLE PRECISION NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    immutable           BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT extracted_propositions_run_client_ref_unique
        UNIQUE (extraction_run_id, client_ref),
    CONSTRAINT extracted_propositions_client_ref_format CHECK (
        client_ref ~ '^[a-z][a-z0-9_\-]{0,127}$'
    ),
    CONSTRAINT extracted_propositions_prop_type_check CHECK (
        prop_type IN (
            'charge',
            'rule',
            'finding',
            'legal_test',
            'aggravating_factor',
            'mitigating_factor',
            'sanction',
            'costs',
            'authority',
            'appeal_status'
        )
    ),
    CONSTRAINT extracted_propositions_epistemic_check CHECK (
        epistemic_class IN ('fact', 'interpretation')
    ),
    CONSTRAINT extracted_propositions_derivation_check CHECK (
        derivation IN ('verbatim', 'normalized', 'inferred')
    ),
    CONSTRAINT extracted_propositions_confidence_range CHECK (
        confidence >= 0 AND confidence <= 1
    ),
    CONSTRAINT extracted_propositions_claim_nonempty CHECK (length(trim(claim_text)) > 0),
    CONSTRAINT extracted_propositions_legal_test_interpretation CHECK (
        prop_type <> 'legal_test' OR epistemic_class = 'interpretation'
    ),
    CONSTRAINT extracted_propositions_immutable_true CHECK (immutable = TRUE)
);

COMMENT ON TABLE extracted_propositions IS
    'Immutable machine extraction outputs. Edits never mutate these rows — append '
    'proposition_revisions instead.';

CREATE INDEX extracted_propositions_decision_id_idx
    ON extracted_propositions (decision_id);
CREATE INDEX extracted_propositions_prop_type_idx
    ON extracted_propositions (prop_type);

CREATE TABLE proposition_evidence (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extracted_proposition_id    UUID NOT NULL REFERENCES extracted_propositions (id)
                                ON DELETE CASCADE,
    document_span_id            UUID NOT NULL REFERENCES document_spans (id),
    page_no                     INTEGER NOT NULL CHECK (page_no >= 1),
    quote_text                  TEXT NOT NULL,
    char_start                  INTEGER CHECK (char_start IS NULL OR char_start >= 0),
    char_end                    INTEGER CHECK (char_end IS NULL OR char_end >= 0),
    relevance                   TEXT,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT proposition_evidence_quote_nonempty CHECK (length(trim(quote_text)) > 0),
    CONSTRAINT proposition_evidence_offsets_pair CHECK (
        (char_start IS NULL AND char_end IS NULL)
        OR (char_start IS NOT NULL AND char_end IS NOT NULL AND char_end >= char_start)
    ),
    CONSTRAINT proposition_evidence_unique
        UNIQUE (extracted_proposition_id, document_span_id, quote_text)
);

COMMENT ON TABLE proposition_evidence IS
    'Evidence links for extracted propositions. Publish/review gates require ≥1 row.';

CREATE INDEX proposition_evidence_span_id_idx
    ON proposition_evidence (document_span_id);

CREATE TABLE proposition_relations (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_run_id           UUID NOT NULL REFERENCES extraction_runs (id) ON DELETE CASCADE,
    from_proposition_id         UUID NOT NULL REFERENCES extracted_propositions (id)
                                ON DELETE CASCADE,
    to_proposition_id           UUID NOT NULL REFERENCES extracted_propositions (id)
                                ON DELETE CASCADE,
    relation_type               TEXT NOT NULL,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT proposition_relations_type_check CHECK (
        relation_type IN (
            'finding_resolves_charge',
            'sanction_applies_to_charge',
            'rule_governs_charge',
            'authority_supports_legal_test',
            'factor_affects_sanction'
        )
    ),
    CONSTRAINT proposition_relations_no_self CHECK (from_proposition_id <> to_proposition_id),
    CONSTRAINT proposition_relations_unique
        UNIQUE (extraction_run_id, from_proposition_id, to_proposition_id, relation_type)
);

CREATE INDEX proposition_relations_from_idx ON proposition_relations (from_proposition_id);
CREATE INDEX proposition_relations_to_idx ON proposition_relations (to_proposition_id);

-- ===========================================================================
-- Append-only proposition revisions (Studio editable layer)
-- ===========================================================================

CREATE TABLE proposition_revisions (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extracted_proposition_id    UUID NOT NULL REFERENCES extracted_propositions (id),
    decision_id                 UUID NOT NULL REFERENCES decisions (id),
    revision_number             INTEGER NOT NULL CHECK (revision_number >= 1),
    supersedes_revision_id      UUID REFERENCES proposition_revisions (id),
    origin                      TEXT NOT NULL,
    prop_type                   TEXT NOT NULL,
    epistemic_class             TEXT NOT NULL,
    derivation                  TEXT NOT NULL,
    claim_text                  TEXT NOT NULL,
    structured_json             JSONB,
    created_by_user_id          UUID,  -- FK added after users table
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    immutable                   BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT proposition_revisions_prop_unique
        UNIQUE (extracted_proposition_id, revision_number),
    CONSTRAINT proposition_revisions_origin_check CHECK (
        origin IN ('extracted', 'human_edited')
    ),
    CONSTRAINT proposition_revisions_prop_type_check CHECK (
        prop_type IN (
            'charge',
            'rule',
            'finding',
            'legal_test',
            'aggravating_factor',
            'mitigating_factor',
            'sanction',
            'costs',
            'authority',
            'appeal_status'
        )
    ),
    CONSTRAINT proposition_revisions_epistemic_check CHECK (
        epistemic_class IN ('fact', 'interpretation')
    ),
    CONSTRAINT proposition_revisions_derivation_check CHECK (
        derivation IN ('verbatim', 'normalized', 'inferred')
    ),
    CONSTRAINT proposition_revisions_claim_nonempty CHECK (length(trim(claim_text)) > 0),
    CONSTRAINT proposition_revisions_supersede_chain CHECK (
        (revision_number = 1 AND supersedes_revision_id IS NULL)
        OR (revision_number > 1 AND supersedes_revision_id IS NOT NULL)
    )
);

COMMENT ON TABLE proposition_revisions IS
    'Append-only claim revisions. origin=extracted for run output; human_edited for '
    'reviewer edits. Rows are immutable (immutable=true); never UPDATE claim_text.';

CREATE INDEX proposition_revisions_decision_id_idx
    ON proposition_revisions (decision_id);
CREATE INDEX proposition_revisions_supersedes_idx
    ON proposition_revisions (supersedes_revision_id);

ALTER TABLE proposition_revisions
    ADD COLUMN claim_tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', coalesce(claim_text, ''))) STORED;

CREATE INDEX proposition_revisions_claim_tsv_idx
    ON proposition_revisions USING GIN (claim_tsv);

-- ===========================================================================
-- Auth (created before reviews FK to users)
-- ===========================================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        TEXT NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    display_name    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT users_username_unique UNIQUE (username),
    CONSTRAINT users_username_nonempty CHECK (length(trim(username)) > 0),
    CONSTRAINT users_password_hash_nonempty CHECK (length(password_hash) > 0),
    CONSTRAINT users_role_check CHECK (
        role IN ('reviewer', 'publisher', 'admin')
    )
);

COMMENT ON TABLE users IS
    'Studio operators. Roles: reviewer (accept/edit), publisher (release), admin.';

ALTER TABLE proposition_revisions
    ADD CONSTRAINT proposition_revisions_created_by_user_fk
    FOREIGN KEY (created_by_user_id) REFERENCES users (id);

CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash      TEXT NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ,
    user_agent      TEXT,
    ip_address      TEXT,
    CONSTRAINT sessions_token_hash_unique UNIQUE (token_hash),
    CONSTRAINT sessions_token_hash_nonempty CHECK (length(trim(token_hash)) > 0),
    CONSTRAINT sessions_expires_after_created CHECK (expires_at > created_at)
);

COMMENT ON TABLE sessions IS
    'Studio cookie sessions. token_hash is a one-way digest of the session secret; '
    'revoke by setting revoked_at.';

CREATE INDEX sessions_user_id_idx ON sessions (user_id);
CREATE INDEX sessions_expires_at_idx ON sessions (expires_at);

CREATE TABLE login_attempts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        TEXT NOT NULL,
    succeeded       BOOLEAN NOT NULL,
    ip_address      TEXT,
    user_agent      TEXT,
    failure_reason  TEXT,
    attempted_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE login_attempts IS
    'Append-only auth attempt log for rate-limiting and audit.';

CREATE INDEX login_attempts_username_attempted_at_idx
    ON login_attempts (username, attempted_at DESC);
CREATE INDEX login_attempts_attempted_at_idx
    ON login_attempts (attempted_at DESC);

-- ===========================================================================
-- Reviews
-- ===========================================================================

CREATE TABLE reviews (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id                 UUID NOT NULL REFERENCES decisions (id) ON DELETE CASCADE,
    proposition_revision_id     UUID NOT NULL REFERENCES proposition_revisions (id),
    extracted_proposition_id    UUID NOT NULL REFERENCES extracted_propositions (id),
    reviewer_user_id            UUID NOT NULL REFERENCES users (id),
    review_status               TEXT NOT NULL,
    notes                       TEXT,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT reviews_status_check CHECK (
        review_status IN ('pending', 'accepted', 'edited', 'rejected')
    )
);

COMMENT ON TABLE reviews IS
    'Human review actions against a proposition_revision. Default ingest state is pending; '
    'production paths must not auto-accept model output.';

CREATE INDEX reviews_decision_id_idx ON reviews (decision_id);
CREATE INDEX reviews_proposition_revision_id_idx ON reviews (proposition_revision_id);
CREATE INDEX reviews_reviewer_user_id_idx ON reviews (reviewer_user_id);
CREATE INDEX reviews_status_idx ON reviews (review_status);

CREATE UNIQUE INDEX reviews_one_open_pending_uidx
    ON reviews (proposition_revision_id)
    WHERE review_status = 'pending';

-- ===========================================================================
-- Editorial annotations (taxonomy classifications for release)
-- ===========================================================================

CREATE TABLE editorial_annotations (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id             UUID REFERENCES decisions (id) ON DELETE SET NULL,
    external_ref            TEXT NOT NULL,
    regulator_code          TEXT NOT NULL,
    taxonomy_version        TEXT NOT NULL,
    issue_categories        JSONB NOT NULL DEFAULT '[]'::jsonb,
    finding_outcomes        JSONB NOT NULL DEFAULT '[]'::jsonb,
    sanction_categories     JSONB NOT NULL DEFAULT '[]'::jsonb,
    factor_categories       JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary                 TEXT NOT NULL,
    takeaway                TEXT NOT NULL,
    supporting_client_refs  JSONB NOT NULL DEFAULT '[]'::jsonb,
    reviewer_status         TEXT NOT NULL,
    created_by_user_id      UUID REFERENCES users (id),
    updated_by_user_id      UUID REFERENCES users (id),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT editorial_annotations_external_ref_unique UNIQUE (external_ref),
    CONSTRAINT editorial_annotations_regulator_check CHECK (
        regulator_code IN ('MCHK', 'DCHK')
    ),
    CONSTRAINT editorial_annotations_reviewer_status_check CHECK (
        reviewer_status IN (
            'verified',
            'human_edited',
            'incomplete',
            'disputed',
            'superseded'
        )
    ),
    CONSTRAINT editorial_annotations_issue_categories_array CHECK (
        jsonb_typeof(issue_categories) = 'array'
    ),
    CONSTRAINT editorial_annotations_finding_outcomes_array CHECK (
        jsonb_typeof(finding_outcomes) = 'array'
    ),
    CONSTRAINT editorial_annotations_sanction_categories_array CHECK (
        jsonb_typeof(sanction_categories) = 'array'
    ),
    CONSTRAINT editorial_annotations_factor_categories_array CHECK (
        jsonb_typeof(factor_categories) = 'array'
    ),
    CONSTRAINT editorial_annotations_supporting_refs_array CHECK (
        jsonb_typeof(supporting_client_refs) = 'array'
    ),
    CONSTRAINT editorial_annotations_summary_nonempty CHECK (length(trim(summary)) > 0),
    CONSTRAINT editorial_annotations_takeaway_nonempty CHECK (length(trim(takeaway)) > 0),
    CONSTRAINT editorial_annotations_external_ref_nonempty CHECK (
        length(trim(external_ref)) > 0
    )
);

COMMENT ON TABLE editorial_annotations IS
    'Human taxonomy + editorial takeaway keyed by stable external_ref (survives re-extraction). '
    'Category arrays are JSONB with type checks; codes validated against taxonomy at write time.';

CREATE INDEX editorial_annotations_decision_id_idx
    ON editorial_annotations (decision_id);
CREATE INDEX editorial_annotations_regulator_code_idx
    ON editorial_annotations (regulator_code);

-- Optional normalised category rows for filtering (mirrors JSONB arrays)
CREATE TABLE editorial_annotation_categories (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    editorial_annotation_id     UUID NOT NULL REFERENCES editorial_annotations (id)
                                ON DELETE CASCADE,
    category_kind               TEXT NOT NULL,
    category_code               TEXT NOT NULL,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT editorial_annotation_categories_kind_check CHECK (
        category_kind IN (
            'issue',
            'finding_outcome',
            'sanction',
            'factor'
        )
    ),
    CONSTRAINT editorial_annotation_categories_code_nonempty CHECK (
        length(trim(category_code)) > 0
    ),
    CONSTRAINT editorial_annotation_categories_unique
        UNIQUE (editorial_annotation_id, category_kind, category_code)
);

CREATE INDEX editorial_annotation_categories_code_idx
    ON editorial_annotation_categories (category_kind, category_code);

-- ===========================================================================
-- Publication releases (trusted transaction feeding RC1 contract)
-- ===========================================================================

CREATE TABLE publication_releases (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    release_id              TEXT NOT NULL,
    schema_version          TEXT NOT NULL DEFAULT '1.0.0',
    release_mode            TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'draft',
    version                 INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    title                   TEXT NOT NULL,
    description             TEXT NOT NULL,
    corpus                  TEXT NOT NULL,
    methodology_version     TEXT NOT NULL,
    taxonomy_version        TEXT NOT NULL,
    inclusion_criteria      TEXT NOT NULL,
    exclusion_criteria      TEXT NOT NULL,
    global_caveats          JSONB NOT NULL DEFAULT '[]'::jsonb,
    regulators              JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_cutoff_date      DATE,
    generated_at            TIMESTAMPTZ,
    released_at             TIMESTAMPTZ,
    decision_count          INTEGER NOT NULL DEFAULT 0 CHECK (decision_count >= 0),
    proposition_count       INTEGER NOT NULL DEFAULT 0 CHECK (proposition_count >= 0),
    manifest_sha256         TEXT,
    output_path             TEXT,
    created_by_user_id      UUID REFERENCES users (id),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT publication_releases_release_id_unique UNIQUE (release_id),
    CONSTRAINT publication_releases_release_id_format CHECK (
        release_id ~ '^[a-z0-9][a-z0-9._-]{0,127}$'
    ),
    CONSTRAINT publication_releases_mode_check CHECK (
        release_mode IN ('synthetic_demo', 'public')
    ),
    CONSTRAINT publication_releases_status_check CHECK (
        status IN (
            'draft',
            'building',
            'ready',
            'published',
            'failed',
            'superseded'
        )
    ),
    CONSTRAINT publication_releases_global_caveats_array CHECK (
        jsonb_typeof(global_caveats) = 'array'
    ),
    CONSTRAINT publication_releases_regulators_array CHECK (
        jsonb_typeof(regulators) = 'array'
    ),
    CONSTRAINT publication_releases_manifest_sha256_hex CHECK (
        manifest_sha256 IS NULL OR manifest_sha256 ~ '^[a-f0-9]{64}$'
    ),
    CONSTRAINT publication_releases_title_nonempty CHECK (length(trim(title)) > 0)
);

COMMENT ON TABLE publication_releases IS
    'Trusted Studio publication transaction. version supports optimistic concurrency. '
    'Artifacts must conform to frozen publication_release.v1; Observatory reads only '
    'the emitted bundle, never this table directly.';

CREATE INDEX publication_releases_status_idx ON publication_releases (status);
CREATE INDEX publication_releases_mode_idx ON publication_releases (release_mode);

CREATE TABLE publication_release_items (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publication_release_id  UUID NOT NULL REFERENCES publication_releases (id)
                            ON DELETE CASCADE,
    decision_id             UUID NOT NULL REFERENCES decisions (id),
    external_ref            TEXT NOT NULL,
    public_slug             TEXT NOT NULL,
    public_decision_path    TEXT NOT NULL,
    artifact_sha256         TEXT NOT NULL,
    included                BOOLEAN NOT NULL DEFAULT TRUE,
    exclusion_reason        TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT publication_release_items_release_decision_unique
        UNIQUE (publication_release_id, decision_id),
    CONSTRAINT publication_release_items_release_slug_unique
        UNIQUE (publication_release_id, public_slug),
    CONSTRAINT publication_release_items_artifact_sha256_hex CHECK (
        artifact_sha256 ~ '^[a-f0-9]{64}$'
    ),
    CONSTRAINT publication_release_items_slug_nonempty CHECK (
        length(trim(public_slug)) > 0
    ),
    CONSTRAINT publication_release_items_exclusion_consistency CHECK (
        (included = TRUE AND exclusion_reason IS NULL)
        OR (included = FALSE AND exclusion_reason IS NOT NULL)
    )
);

CREATE INDEX publication_release_items_decision_id_idx
    ON publication_release_items (decision_id);
CREATE INDEX publication_release_items_external_ref_idx
    ON publication_release_items (external_ref);

-- ===========================================================================
-- Jobs (lease / retry worker queue)
-- ===========================================================================

CREATE TABLE jobs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type            TEXT NOT NULL,
    dedupe_key          TEXT NOT NULL,
    payload_json        JSONB NOT NULL DEFAULT '{}'::jsonb,
    status              TEXT NOT NULL DEFAULT 'pending',
    attempts            INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    max_attempts        INTEGER NOT NULL DEFAULT 5 CHECK (max_attempts >= 1),
    lease_owner         TEXT,
    lease_expires_at    TIMESTAMPTZ,
    available_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_error          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at          TIMESTAMPTZ,
    finished_at         TIMESTAMPTZ,
    CONSTRAINT jobs_dedupe_key_unique UNIQUE (dedupe_key),
    CONSTRAINT jobs_dedupe_key_nonempty CHECK (length(trim(dedupe_key)) > 0),
    CONSTRAINT jobs_status_check CHECK (
        status IN ('pending', 'running', 'succeeded', 'failed', 'cancelled')
    ),
    CONSTRAINT jobs_payload_object CHECK (jsonb_typeof(payload_json) = 'object'),
    CONSTRAINT jobs_lease_pair CHECK (
        (lease_owner IS NULL AND lease_expires_at IS NULL)
        OR (lease_owner IS NOT NULL AND lease_expires_at IS NOT NULL)
    ),
    CONSTRAINT jobs_job_type_nonempty CHECK (length(trim(job_type)) > 0)
);

COMMENT ON TABLE jobs IS
    'Idempotent job queue with lease_owner / lease_expires_at for SKIP LOCKED workers, '
    'available_at for delayed retry, and unique dedupe_key.';

CREATE INDEX jobs_status_available_at_idx
    ON jobs (status, available_at)
    WHERE status IN ('pending', 'running');
CREATE INDEX jobs_lease_expires_at_idx
    ON jobs (lease_expires_at)
    WHERE status = 'running';
CREATE INDEX jobs_job_type_idx ON jobs (job_type);

-- ===========================================================================
-- Audit events (append-only; revoke UPDATE/DELETE via grants later)
-- ===========================================================================

CREATE TABLE audit_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor           TEXT NOT NULL,
    actor_user_id   UUID REFERENCES users (id) ON DELETE SET NULL,
    action          TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    before_json     JSONB,
    after_json      JSONB,
    request_id      TEXT,
    ip_address      TEXT,
    at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT audit_events_actor_nonempty CHECK (length(trim(actor)) > 0),
    CONSTRAINT audit_events_action_nonempty CHECK (length(trim(action)) > 0),
    CONSTRAINT audit_events_entity_type_nonempty CHECK (length(trim(entity_type)) > 0),
    CONSTRAINT audit_events_entity_id_nonempty CHECK (length(trim(entity_id)) > 0)
);

COMMENT ON TABLE audit_events IS
    'Append-only operational audit log. Application roles should GRANT INSERT/SELECT only '
    '(no UPDATE/DELETE) once privileges are wired.';

CREATE INDEX audit_events_at_idx ON audit_events (at DESC);
CREATE INDEX audit_events_entity_idx ON audit_events (entity_type, entity_id);
CREATE INDEX audit_events_actor_user_id_idx ON audit_events (actor_user_id);
CREATE INDEX audit_events_action_idx ON audit_events (action);

-- ===========================================================================
-- Seed: MVP regulators & source collections
-- ===========================================================================

INSERT INTO regulators (code, name, homepage_url) VALUES
    ('MCHK', 'Medical Council of Hong Kong', 'https://www.mchk.org.hk/'),
    ('DCHK', 'Dental Council of Hong Kong', 'https://www.dchk.org.hk/');

INSERT INTO source_collections (
    regulator_id,
    source_id,
    collection_name,
    index_url,
    visibility,
    consent_status,
    max_excerpt_chars,
    attribution_required,
    terms_reviewed_at,
    notes
)
SELECT
    r.id,
    v.source_id,
    v.collection_name,
    v.index_url,
    'internal_only',
    'not_requested',
    280,
    TRUE,
    now(),
    v.notes
FROM regulators r
JOIN (
    VALUES
        (
            'MCHK',
            'mchk_judgments',
            'Judgments of disciplinary inquiries',
            'https://www.mchk.org.hk/english/complaint/disciplinary.php?type=j',
            'Fixture-only MVP. Commercial republication requires prior written consent. '
            'consent_status remains not_requested until outreach completes.'
        ),
        (
            'DCHK',
            'dchk_judgments',
            'Judgments of disciplinary inquiries',
            'https://www.dchk.org.hk/en/complaints_disciplinary/judgments.html',
            'Fixture-only MVP. Treat commercial use as consent-required until confirmed. '
            'consent_status remains not_requested until outreach completes.'
        )
) AS v(code, source_id, collection_name, index_url, notes)
  ON r.code = v.code;
