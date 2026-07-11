-- RegLens HK Milestone 1 schema
-- PostgreSQL 16+ with pgvector

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TABLE regulators (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    homepage_url    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE sources (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    regulator_id        UUID NOT NULL REFERENCES regulators(id),
    source_id           TEXT NOT NULL UNIQUE,
    index_url           TEXT,
    licence_status      TEXT NOT NULL DEFAULT 'internal_use_only',
    terms_reviewed_at   TIMESTAMPTZ,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       UUID NOT NULL REFERENCES sources(id),
    external_ref    TEXT,
    title           TEXT,
    decision_date   DATE,
    hearing_dates   DATE[],
    language        TEXT NOT NULL DEFAULT 'en',
    mime_type       TEXT NOT NULL,
    byte_size       BIGINT NOT NULL,
    sha256          TEXT NOT NULL,
    storage_key     TEXT NOT NULL,
    ingest_status   TEXT NOT NULL DEFAULT 'stored',
    text_quality    TEXT,
    ocr_used        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    immutable       BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT documents_sha256_hex CHECK (sha256 ~ '^[a-f0-9]{64}$'),
    CONSTRAINT documents_sha256_unique UNIQUE (sha256)
);

CREATE UNIQUE INDEX documents_storage_key_uidx ON documents (storage_key);

CREATE TABLE document_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(id),
    sha256          TEXT NOT NULL,
    storage_key     TEXT NOT NULL,
    acquired_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    note            TEXT
);

CREATE TABLE document_spans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_no         INTEGER NOT NULL CHECK (page_no >= 1),
    span_type       TEXT NOT NULL DEFAULT 'page'
                    CHECK (span_type IN ('page', 'block', 'paragraph')),
    char_start      INTEGER,
    char_end        INTEGER,
    text            TEXT NOT NULL,
    text_hash       TEXT NOT NULL,
    bbox_json       JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, page_no, span_type, text_hash)
);

CREATE TABLE practitioners (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    regulator_id        UUID NOT NULL REFERENCES regulators(id),
    registration_no     TEXT,
    display_name        TEXT NOT NULL,
    profession          TEXT NOT NULL CHECK (profession IN ('doctor', 'dentist')),
    normalized_name     TEXT NOT NULL,
    UNIQUE (regulator_id, registration_no)
);

CREATE TABLE decisions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id             UUID NOT NULL UNIQUE REFERENCES documents(id),
    regulator_id            UUID NOT NULL REFERENCES regulators(id),
    case_ref                TEXT,
    decision_date           DATE,
    profession              TEXT CHECK (profession IN ('doctor', 'dentist')),
    appeal_status_as_stated TEXT,
    published_at            TIMESTAMPTZ,
    coverage_json           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE decision_practitioners (
    decision_id     UUID NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    practitioner_id UUID NOT NULL REFERENCES practitioners(id),
    role            TEXT NOT NULL DEFAULT 'defendant',
    PRIMARY KEY (decision_id, practitioner_id, role)
);

CREATE TABLE extraction_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         UUID NOT NULL REFERENCES documents(id),
    pipeline_version    TEXT NOT NULL,
    model_provider      TEXT NOT NULL,
    model_version       TEXT NOT NULL,
    prompt_version      TEXT NOT NULL,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at         TIMESTAMPTZ,
    status              TEXT NOT NULL DEFAULT 'running',
    input_hash          TEXT NOT NULL,
    UNIQUE (document_id, input_hash)
);

CREATE TABLE propositions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id         UUID NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    extraction_run_id   UUID NOT NULL REFERENCES extraction_runs(id),
    prop_type           TEXT NOT NULL,
    epistemic_class     TEXT NOT NULL CHECK (epistemic_class IN ('fact', 'interpretation')),
    claim_text          TEXT NOT NULL,
    structured_json     JSONB,
    confidence          DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    review_status       TEXT NOT NULL DEFAULT 'pending'
                        CHECK (review_status IN ('pending', 'accepted', 'edited', 'rejected')),
    reviewed_by         TEXT,
    reviewed_at         TIMESTAMPTZ,
    published           BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE proposition_spans (
    proposition_id  UUID NOT NULL REFERENCES propositions(id) ON DELETE CASCADE,
    span_id         UUID NOT NULL REFERENCES document_spans(id),
    quote_text      TEXT NOT NULL,
    relevance       TEXT,
    PRIMARY KEY (proposition_id, span_id, quote_text)
);

-- Publish gate: published propositions must be reviewed.
-- Span presence is enforced in application code + tests (referential rows in proposition_spans).
ALTER TABLE propositions
    ADD CONSTRAINT propositions_publish_requires_review
    CHECK (
        published = FALSE
        OR review_status IN ('accepted', 'edited')
    );

CREATE TABLE embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_type  TEXT NOT NULL CHECK (owner_type IN ('span', 'proposition', 'decision_summary')),
    owner_id    UUID NOT NULL,
    model       TEXT NOT NULL,
    dims        INTEGER NOT NULL,
    embedding   vector(384),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type        TEXT NOT NULL,
    dedupe_key      TEXT NOT NULL UNIQUE,
    payload_json    JSONB NOT NULL DEFAULT '{}'::jsonb,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'running', 'succeeded', 'failed', 'cancelled')),
    attempts        INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ
);

CREATE TABLE audit_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor       TEXT NOT NULL,
    action      TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id   TEXT NOT NULL,
    before_json JSONB,
    after_json  JSONB,
    at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE review_queue_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposition_id  UUID NOT NULL REFERENCES propositions(id) ON DELETE CASCADE,
    decision_id     UUID NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    priority        INTEGER NOT NULL DEFAULT 100,
    reason          TEXT,
    status          TEXT NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open', 'done', 'cancelled')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE coverage_warnings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    code        TEXT NOT NULL,
    message     TEXT NOT NULL,
    severity    TEXT NOT NULL DEFAULT 'info'
                CHECK (severity IN ('info', 'warning', 'error')),
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Full-text search helper on span text
ALTER TABLE document_spans ADD COLUMN text_tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', coalesce(text, ''))) STORED;
CREATE INDEX document_spans_tsv_idx ON document_spans USING GIN (text_tsv);

-- Seed MVP regulators and sources (internal-use licence posture)
INSERT INTO regulators (code, name, homepage_url) VALUES
    ('MCHK', 'Medical Council of Hong Kong', 'https://www.mchk.org.hk/'),
    ('DCHK', 'Dental Council of Hong Kong', 'https://www.dchk.org.hk/');

INSERT INTO sources (regulator_id, source_id, index_url, licence_status, terms_reviewed_at, notes)
SELECT r.id, v.source_id, v.index_url, 'internal_use_only', now(), v.notes
FROM regulators r
JOIN (
    VALUES
        ('MCHK', 'mchk_judgments',
         'https://www.mchk.org.hk/english/complaint/disciplinary.php?type=j',
         'Fixture-only MVP. Commercial republication requires prior written consent.'),
        ('DCHK', 'dchk_judgments',
         'https://www.dchk.org.hk/en/complaints_disciplinary/judgments.html',
         'Fixture-only MVP. Treat commercial use as consent-required until confirmed.')
) AS v(code, source_id, index_url, notes)
  ON r.code = v.code;
