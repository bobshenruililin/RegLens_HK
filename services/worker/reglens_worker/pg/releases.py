"""Publication release draft / validate / approve transaction (fail closed)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .decisions import public_slug_from_external_ref

# Schema CHECK allows draft|building|ready|published|failed|superseded.
# "Approved for build" maps to ready (no separate approved status in baseline).
APPROVED_STATUS = "ready"
_PLACEHOLDER_SHA256 = "0" * 64
_PUBLISHABLE = frozenset({"accepted", "edited"})


class ReleaseRepoError(ValueError):
    """Unsafe or invalid publication release transition."""


def create_draft_release(
    conn: psycopg.Connection,
    *,
    release_id: str,
    release_mode: str,
    title: str,
    description: str,
    corpus: str,
    methodology_version: str,
    taxonomy_version: str,
    inclusion_criteria: str,
    exclusion_criteria: str,
    global_caveats: list[str] | None = None,
    regulators: list[str] | None = None,
    source_cutoff_date: date | None = None,
    created_by_user_id: uuid.UUID | str | None = None,
    schema_version: str = "1.0.0",
) -> dict[str, Any]:
    if release_mode not in {"synthetic_demo", "public"}:
        raise ReleaseRepoError(f"Invalid release_mode={release_mode!r}")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO publication_releases (
                release_id, schema_version, release_mode, status, version,
                title, description, corpus, methodology_version, taxonomy_version,
                inclusion_criteria, exclusion_criteria, global_caveats, regulators,
                source_cutoff_date, created_by_user_id
            ) VALUES (
                %s, %s, %s, 'draft', 1,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
            RETURNING *
            """,
            (
                release_id,
                schema_version,
                release_mode,
                title,
                description,
                corpus,
                methodology_version,
                taxonomy_version,
                inclusion_criteria,
                exclusion_criteria,
                Jsonb(global_caveats or []),
                Jsonb(regulators or []),
                source_cutoff_date,
                created_by_user_id,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise ReleaseRepoError("create_draft_release returned no row")
        return dict(row)


def add_release_item(
    conn: psycopg.Connection,
    *,
    publication_release_id: uuid.UUID | str,
    decision_id: uuid.UUID | str,
    included: bool = True,
    exclusion_reason: str | None = None,
) -> dict[str, Any]:
    """Attach a decision to a draft release (artifact hash filled at build time)."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT d.external_ref, d.id
            FROM decisions d
            WHERE d.id = %s
            """,
            (decision_id,),
        )
        decision = cur.fetchone()
        if decision is None:
            raise ReleaseRepoError(f"Unknown decision_id={decision_id}")
        external_ref = decision["external_ref"]
        slug = public_slug_from_external_ref(external_ref)
        if included and exclusion_reason:
            raise ReleaseRepoError("included items must not have exclusion_reason")
        if not included and not exclusion_reason:
            raise ReleaseRepoError("excluded items require exclusion_reason")

        cur.execute(
            """
            INSERT INTO publication_release_items (
                publication_release_id, decision_id, external_ref, public_slug,
                public_decision_path, artifact_sha256, included, exclusion_reason
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (publication_release_id, decision_id) DO UPDATE SET
                included = EXCLUDED.included,
                exclusion_reason = EXCLUDED.exclusion_reason,
                public_slug = EXCLUDED.public_slug,
                public_decision_path = EXCLUDED.public_decision_path
            RETURNING *
            """,
            (
                publication_release_id,
                decision_id,
                external_ref,
                slug,
                f"decisions/{slug}.json",
                _PLACEHOLDER_SHA256,
                included,
                exclusion_reason,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise ReleaseRepoError("add_release_item returned no row")
        return dict(row)


def get_release(
    conn: psycopg.Connection,
    *,
    release_id: str | None = None,
    publication_release_id: uuid.UUID | str | None = None,
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        if publication_release_id is not None:
            cur.execute(
                "SELECT * FROM publication_releases WHERE id = %s",
                (publication_release_id,),
            )
        elif release_id is not None:
            cur.execute(
                "SELECT * FROM publication_releases WHERE release_id = %s",
                (release_id,),
            )
        else:
            raise ReleaseRepoError("release_id or publication_release_id required")
        row = cur.fetchone()
        return dict(row) if row else None


def list_release_items(
    conn: psycopg.Connection,
    publication_release_id: uuid.UUID | str,
    *,
    included_only: bool = True,
) -> list[dict[str, Any]]:
    sql = """
        SELECT i.*, d.fixture_kind, d.profession, d.title AS decision_title,
               d.official_source_url, sc.source_id, sc.visibility, sc.consent_status,
               sc.max_excerpt_chars, r.code AS regulator_code
        FROM publication_release_items i
        JOIN decisions d ON d.id = i.decision_id
        JOIN source_collections sc ON sc.id = d.source_collection_id
        JOIN regulators r ON r.id = d.regulator_id
        WHERE i.publication_release_id = %s
    """
    params: list[Any] = [publication_release_id]
    if included_only:
        sql += " AND i.included = TRUE"
    sql += " ORDER BY i.public_slug"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def _head_revisions_for_decision(
    cur: Any,
    decision_id: uuid.UUID | str,
) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT DISTINCT ON (pr.extracted_proposition_id)
            pr.*,
            ep.client_ref,
            (
                SELECT rv.review_status
                FROM reviews rv
                WHERE rv.proposition_revision_id = pr.id
                ORDER BY rv.created_at DESC
                LIMIT 1
            ) AS latest_review_status,
            (
                SELECT COUNT(*)::int
                FROM proposition_evidence pe
                WHERE pe.extracted_proposition_id = pr.extracted_proposition_id
            ) AS evidence_count
        FROM proposition_revisions pr
        JOIN extracted_propositions ep ON ep.id = pr.extracted_proposition_id
        WHERE pr.decision_id = %s
        ORDER BY pr.extracted_proposition_id, pr.revision_number DESC
        """,
        (decision_id,),
    )
    return [dict(row) for row in cur.fetchall()]


def validate_release(
    conn: psycopg.Connection,
    *,
    publication_release_id: uuid.UUID | str,
    selected_revision_ids: list[uuid.UUID | str] | None = None,
) -> list[str]:
    """
    Fail-closed RC2 validation. Returns a list of error strings (empty = ok).

    Core rules:
    - release exists and is draft|ready|building
    - at least one included item
    - fixture_kind matches release_mode (no mixed corpus)
    - public mode refuses internal_only sources / synthetic fixtures
    - every selected (or head) revision is accepted/edited with ≥1 evidence
    - editorial annotation present for each included decision
    """
    errors: list[str] = []
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM publication_releases WHERE id = %s",
            (publication_release_id,),
        )
        release = cur.fetchone()
        if release is None:
            return [f"Unknown publication_release id={publication_release_id}"]

        items = list_release_items(conn, publication_release_id, included_only=True)
        if not items:
            errors.append("Release has no included decisions")

        kinds: set[str] = set()
        selected_set = (
            {str(x) for x in selected_revision_ids} if selected_revision_ids is not None else None
        )

        for item in items:
            kinds.add(item["fixture_kind"])
            if release["release_mode"] == "synthetic_demo" and item["fixture_kind"] != "synthetic":
                errors.append(
                    f"synthetic_demo refuses non-synthetic decision {item['decision_id']} "
                    f"fixture_kind={item['fixture_kind']!r}"
                )
            if release["release_mode"] == "public":
                if item["fixture_kind"] == "synthetic":
                    errors.append(
                        f"public release refuses synthetic decision {item['decision_id']}"
                    )
                if item["visibility"] == "internal_only":
                    errors.append(
                        f"Source {item['source_id']} is internal_only; "
                        f"cannot include decision {item['decision_id']}"
                    )
                if not item.get("official_source_url"):
                    errors.append(
                        f"Real public decision {item['external_ref']} requires official_source_url"
                    )

            heads = _head_revisions_for_decision(cur, item["decision_id"])
            if not heads:
                errors.append(f"Decision {item['decision_id']} has no proposition revisions")
                continue

            if selected_set is not None:
                selected_heads = [h for h in heads if str(h["id"]) in selected_set]
                if not selected_heads:
                    errors.append(
                        f"Decision {item['decision_id']} has no selected revisions in release"
                    )
                check_rows = selected_heads
            else:
                check_rows = heads

            publishable = 0
            for rev in check_rows:
                status = rev.get("latest_review_status")
                if status not in _PUBLISHABLE:
                    errors.append(
                        f"Revision {rev['id']} ({rev.get('client_ref')}) "
                        f"not accepted/edited (status={status!r})"
                    )
                    continue
                if int(rev.get("evidence_count") or 0) < 1:
                    errors.append(f"Revision {rev['id']} ({rev.get('client_ref')}) has no evidence")
                    continue
                publishable += 1
            if publishable < 1:
                errors.append(
                    f"Decision {item['decision_id']} has no publishable accepted/edited revisions"
                )

            cur.execute(
                """
                SELECT 1 FROM editorial_annotations
                WHERE decision_id = %s OR external_ref = %s
                LIMIT 1
                """,
                (item["decision_id"], item["external_ref"]),
            )
            if cur.fetchone() is None:
                errors.append(
                    f"Missing editorial annotation for decision {item['decision_id']} "
                    f"/ {item['external_ref']}"
                )

        if "synthetic" in kinds and "real" in kinds:
            errors.append("Release mixes synthetic and real material")

    return errors


def approve_and_build_release(
    conn: psycopg.Connection,
    *,
    publication_release_id: uuid.UUID | str,
    expected_version: int,
    selected_revision_ids: list[uuid.UUID | str] | None = None,
    actor_user_id: uuid.UUID | str | None = None,
) -> dict[str, Any]:
    """
    Lock release FOR UPDATE, check optimistic version, validate (fail closed),
    set status to ready (approved-for-build), bump version, return release row.

    The caller / `release_postgres` adapter then compiles the public bundle.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT * FROM publication_releases
            WHERE id = %s
            FOR UPDATE
            """,
            (publication_release_id,),
        )
        release = cur.fetchone()
        if release is None:
            raise ReleaseRepoError(f"Unknown publication_release id={publication_release_id}")

        if int(release["version"]) != int(expected_version):
            raise ReleaseRepoError(
                f"Version conflict: expected={expected_version}, actual={release['version']}"
            )

        if release["status"] not in {"draft", "ready", "failed"}:
            raise ReleaseRepoError(f"Cannot approve release in status={release['status']!r}")

    errors = validate_release(
        conn,
        publication_release_id=publication_release_id,
        selected_revision_ids=selected_revision_ids,
    )
    if errors:
        raise ReleaseRepoError("Release validation failed (fail-closed):\n- " + "\n- ".join(errors))

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            UPDATE publication_releases
            SET status = %s,
                version = version + 1,
                updated_at = now(),
                generated_at = COALESCE(generated_at, now())
            WHERE id = %s
            RETURNING *
            """,
            (APPROVED_STATUS, publication_release_id),
        )
        updated = cur.fetchone()
        if updated is None:
            raise ReleaseRepoError("approve update returned no row")

        # Optional audit trail — imported lazily to avoid cycles at import time.
        if actor_user_id is not None:
            from .audit import insert_audit_event

            insert_audit_event(
                conn,
                actor="publisher",
                action="release.approve",
                entity_type="publication_release",
                entity_id=str(publication_release_id),
                actor_user_id=actor_user_id,
                before_json={"status": release["status"], "version": release["version"]},
                after_json={"status": updated["status"], "version": updated["version"]},
            )

        return dict(updated)


def mark_release_published(
    conn: psycopg.Connection,
    *,
    publication_release_id: uuid.UUID | str,
    expected_version: int,
    manifest_sha256: str,
    output_path: str,
    decision_count: int,
    proposition_count: int,
    released_at: datetime | None = None,
) -> dict[str, Any]:
    """Record successful artifact build against an approved (ready) release."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT * FROM publication_releases
            WHERE id = %s
            FOR UPDATE
            """,
            (publication_release_id,),
        )
        release = cur.fetchone()
        if release is None:
            raise ReleaseRepoError(f"Unknown publication_release id={publication_release_id}")
        if int(release["version"]) != int(expected_version):
            raise ReleaseRepoError(
                f"Version conflict: expected={expected_version}, actual={release['version']}"
            )
        if release["status"] not in {APPROVED_STATUS, "building"}:
            raise ReleaseRepoError(
                f"Cannot publish from status={release['status']!r}; expected {APPROVED_STATUS}"
            )
        cur.execute(
            """
            UPDATE publication_releases
            SET status = 'published',
                version = version + 1,
                manifest_sha256 = %s,
                output_path = %s,
                decision_count = %s,
                proposition_count = %s,
                released_at = COALESCE(%s, now()),
                generated_at = COALESCE(generated_at, now()),
                updated_at = now()
            WHERE id = %s
            RETURNING *
            """,
            (
                manifest_sha256.strip().lower(),
                output_path,
                decision_count,
                proposition_count,
                released_at,
                publication_release_id,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise ReleaseRepoError("mark_release_published returned no row")
        return dict(row)


def update_item_artifact_hash(
    conn: psycopg.Connection,
    *,
    publication_release_id: uuid.UUID | str,
    decision_id: uuid.UUID | str,
    artifact_sha256: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE publication_release_items
            SET artifact_sha256 = %s
            WHERE publication_release_id = %s AND decision_id = %s
            """,
            (artifact_sha256.strip().lower(), publication_release_id, decision_id),
        )
