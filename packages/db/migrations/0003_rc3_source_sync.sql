-- MVP-RC3: policy-gated live-source metadata sync and acquisition audit tables.
--
-- Missing source items are intentionally retained. Sync code may mark rows as
-- status='missing' and set missing_since, but this migration does not define
-- cascade/delete behavior that would remove source history.

-- ===========================================================================
-- Source sync runs
-- ===========================================================================

CREATE TABLE source_sync_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id           TEXT NOT NULL REFERENCES source_collections (source_id),
    adapter_id          TEXT NOT NULL,
    adapter_version     TEXT NOT NULL,
    mode                TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'queued',
    dry_run             BOOLEAN NOT NULL DEFAULT TRUE,
    live                BOOLEAN NOT NULL DEFAULT FALSE,
    policy_snapshot     JSONB NOT NULL DEFAULT '{}'::jsonb,
    request_budget      INTEGER NOT NULL CHECK (request_budget >= 0),
    items_discovered    INTEGER NOT NULL DEFAULT 0 CHECK (items_discovered >= 0),
    items_persisted     INTEGER NOT NULL DEFAULT 0 CHECK (items_persisted >= 0),
    documents_acquired  INTEGER NOT NULL DEFAULT 0 CHECK (documents_acquired >= 0),
    error_message       TEXT,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT source_sync_runs_mode_check CHECK (
        mode IN ('metadata_dry_run', 'metadata_sync', 'document_acquire')
    ),
    CONSTRAINT source_sync_runs_status_check CHECK (
        status IN ('queued', 'running', 'succeeded', 'partial', 'failed', 'cancelled')
    ),
    CONSTRAINT source_sync_runs_policy_snapshot_is_object CHECK (
        jsonb_typeof(policy_snapshot) = 'object'
    ),
    CONSTRAINT source_sync_runs_finished_after_started CHECK (
        finished_at IS NULL OR finished_at >= started_at
    ),
    CONSTRAINT source_sync_runs_adapter_id_nonempty CHECK (length(trim(adapter_id)) > 0),
    CONSTRAINT source_sync_runs_adapter_version_nonempty CHECK (
        length(trim(adapter_version)) > 0
    )
);

COMMENT ON TABLE source_sync_runs IS
    'One policy-gated RC3 source sync/acquire attempt. Retains disabled/failed attempts.';

CREATE INDEX source_sync_runs_source_id_started_at_idx
    ON source_sync_runs (source_id, started_at DESC);
CREATE INDEX source_sync_runs_status_idx ON source_sync_runs (status);
CREATE INDEX source_sync_runs_mode_idx ON source_sync_runs (mode);

-- ===========================================================================
-- Source index snapshots
-- ===========================================================================

CREATE TABLE source_index_snapshots (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id              UUID NOT NULL REFERENCES source_sync_runs (id) ON DELETE CASCADE,
    source_id           TEXT NOT NULL REFERENCES source_collections (source_id),
    index_url           TEXT NOT NULL,
    snapshot_status     TEXT NOT NULL DEFAULT 'parsed',
    fetched_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    http_status         INTEGER CHECK (http_status IS NULL OR http_status BETWEEN 100 AND 599),
    content_sha256      TEXT,
    byte_size           BIGINT CHECK (byte_size IS NULL OR byte_size >= 0),
    item_count          INTEGER NOT NULL DEFAULT 0 CHECK (item_count >= 0),
    parser_health_json  JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw_fixture_path    TEXT,
    storage_path        TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT source_index_snapshots_status_check CHECK (
        snapshot_status IN ('parsed', 'failed', 'skipped')
    ),
    CONSTRAINT source_index_snapshots_sha256_hex CHECK (
        content_sha256 IS NULL OR content_sha256 ~ '^[a-f0-9]{64}$'
    ),
    CONSTRAINT source_index_snapshots_health_is_object CHECK (
        jsonb_typeof(parser_health_json) = 'object'
    ),
    CONSTRAINT source_index_snapshots_index_url_nonempty CHECK (
        length(trim(index_url)) > 0
    )
);

COMMENT ON TABLE source_index_snapshots IS
    'Per-run official index or fixture snapshot metadata. Bytes are stored externally.';

CREATE INDEX source_index_snapshots_run_id_idx ON source_index_snapshots (run_id);
CREATE INDEX source_index_snapshots_source_id_fetched_at_idx
    ON source_index_snapshots (source_id, fetched_at DESC);
CREATE INDEX source_index_snapshots_content_sha256_idx
    ON source_index_snapshots (content_sha256);

-- ===========================================================================
-- Discovered source items
-- ===========================================================================

CREATE TABLE discovered_source_items (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id               TEXT NOT NULL REFERENCES source_collections (source_id),
    source_item_key         TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'seen',
    title                   TEXT,
    source_url              TEXT,
    document_url            TEXT,
    content_sha256          TEXT,
    case_refs               JSONB NOT NULL DEFAULT '[]'::jsonb,
    inquiry_dates           JSONB NOT NULL DEFAULT '[]'::jsonb,
    judgment_date           DATE,
    published_date          DATE,
    metadata_json           JSONB NOT NULL DEFAULT '{}'::jsonb,
    caveats_json            JSONB NOT NULL DEFAULT '[]'::jsonb,
    first_seen_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    missing_since           TIMESTAMPTZ,
    last_sync_run_id        UUID REFERENCES source_sync_runs (id) ON DELETE SET NULL,
    last_snapshot_id        UUID REFERENCES source_index_snapshots (id) ON DELETE SET NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT discovered_source_items_unique_key UNIQUE (source_id, source_item_key),
    CONSTRAINT discovered_source_items_status_check CHECK (
        status IN ('seen', 'changed', 'missing', 'acquired', 'error', 'ignored')
    ),
    CONSTRAINT discovered_source_items_key_nonempty CHECK (
        length(trim(source_item_key)) > 0
    ),
    CONSTRAINT discovered_source_items_sha256_hex CHECK (
        content_sha256 IS NULL OR content_sha256 ~ '^[a-f0-9]{64}$'
    ),
    CONSTRAINT discovered_source_items_case_refs_is_array CHECK (
        jsonb_typeof(case_refs) = 'array'
    ),
    CONSTRAINT discovered_source_items_inquiry_dates_is_array CHECK (
        jsonb_typeof(inquiry_dates) = 'array'
    ),
    CONSTRAINT discovered_source_items_metadata_is_object CHECK (
        jsonb_typeof(metadata_json) = 'object'
    ),
    CONSTRAINT discovered_source_items_caveats_is_array CHECK (
        jsonb_typeof(caveats_json) = 'array'
    ),
    CONSTRAINT discovered_source_items_seen_order_check CHECK (last_seen_at >= first_seen_at)
);

COMMENT ON TABLE discovered_source_items IS
    'Stable official-source item inventory. Missing items are marked, never deleted.';
COMMENT ON COLUMN discovered_source_items.judgment_date IS
    'Published judgment date only. Do not infer this from inquiry/hearing dates.';

CREATE INDEX discovered_source_items_source_id_status_idx
    ON discovered_source_items (source_id, status);
CREATE INDEX discovered_source_items_last_seen_at_idx
    ON discovered_source_items (last_seen_at DESC);
CREATE INDEX discovered_source_items_document_url_idx
    ON discovered_source_items (document_url);
CREATE INDEX discovered_source_items_case_refs_gin_idx
    ON discovered_source_items USING GIN (case_refs);

-- ===========================================================================
-- URL aliases and redirects
-- ===========================================================================

CREATE TABLE source_url_aliases (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id                   TEXT NOT NULL REFERENCES source_collections (source_id),
    discovered_source_item_id   UUID REFERENCES discovered_source_items (id) ON DELETE CASCADE,
    url                         TEXT NOT NULL,
    url_kind                    TEXT NOT NULL DEFAULT 'other',
    first_seen_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_fetch_attempt_id       UUID,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT source_url_aliases_source_url_unique UNIQUE (source_id, url),
    CONSTRAINT source_url_aliases_url_kind_check CHECK (
        url_kind IN ('index', 'detail', 'document', 'redirect', 'canonical', 'other')
    ),
    CONSTRAINT source_url_aliases_url_nonempty CHECK (length(trim(url)) > 0),
    CONSTRAINT source_url_aliases_seen_order_check CHECK (last_seen_at >= first_seen_at)
);

COMMENT ON TABLE source_url_aliases IS
    'Known canonical/detail/document/redirect URLs for source items and indexes.';

CREATE INDEX source_url_aliases_item_id_idx
    ON source_url_aliases (discovered_source_item_id);
CREATE INDEX source_url_aliases_url_kind_idx ON source_url_aliases (url_kind);

-- ===========================================================================
-- Fetch attempts
-- ===========================================================================

CREATE TABLE fetch_attempts (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id                      UUID REFERENCES source_sync_runs (id) ON DELETE SET NULL,
    source_id                   TEXT NOT NULL REFERENCES source_collections (source_id),
    discovered_source_item_id   UUID REFERENCES discovered_source_items (id) ON DELETE SET NULL,
    url                         TEXT NOT NULL,
    final_url                   TEXT,
    purpose                     TEXT NOT NULL,
    status                      TEXT NOT NULL DEFAULT 'queued',
    http_status                 INTEGER CHECK (http_status IS NULL OR http_status BETWEEN 100 AND 599),
    content_type                TEXT,
    byte_size                   BIGINT CHECK (byte_size IS NULL OR byte_size >= 0),
    sha256                      TEXT,
    retry_count                 INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    redirect_count              INTEGER NOT NULL DEFAULT 0 CHECK (redirect_count >= 0),
    storage_path                TEXT,
    error_class                 TEXT,
    error_message               TEXT,
    started_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at                 TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fetch_attempts_purpose_check CHECK (
        purpose IN ('index', 'detail', 'document', 'robots', 'terms')
    ),
    CONSTRAINT fetch_attempts_status_check CHECK (
        status IN ('queued', 'succeeded', 'failed', 'blocked', 'skipped', 'retry_exhausted')
    ),
    CONSTRAINT fetch_attempts_sha256_hex CHECK (
        sha256 IS NULL OR sha256 ~ '^[a-f0-9]{64}$'
    ),
    CONSTRAINT fetch_attempts_url_nonempty CHECK (length(trim(url)) > 0),
    CONSTRAINT fetch_attempts_finished_after_started CHECK (
        finished_at IS NULL OR finished_at >= started_at
    )
);

COMMENT ON TABLE fetch_attempts IS
    'Network/acquisition audit records. Response bodies are never stored in this table.';

ALTER TABLE source_url_aliases
    ADD CONSTRAINT source_url_aliases_last_fetch_attempt_fk
    FOREIGN KEY (last_fetch_attempt_id) REFERENCES fetch_attempts (id) ON DELETE SET NULL;

CREATE INDEX fetch_attempts_run_id_idx ON fetch_attempts (run_id);
CREATE INDEX fetch_attempts_source_id_started_at_idx
    ON fetch_attempts (source_id, started_at DESC);
CREATE INDEX fetch_attempts_item_id_idx ON fetch_attempts (discovered_source_item_id);
CREATE INDEX fetch_attempts_status_idx ON fetch_attempts (status);
CREATE INDEX fetch_attempts_sha256_idx ON fetch_attempts (sha256);
