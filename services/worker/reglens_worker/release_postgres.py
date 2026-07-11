"""Build publication_release.v1 bundles from an approved Postgres release.

Loads selected decisions / head revisions / annotations from PostgreSQL and
reuses the privacy + schema validation path in `release.py`.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from .atomic_io import atomic_write_text
from .hashutil import sha256_bytes
from .pg.releases import (
    APPROVED_STATUS,
    ReleaseRepoError,
    get_release,
    list_release_items,
    mark_release_published,
    update_item_artifact_hash,
)
from .release import (
    METHODOLOGY_VERSION,
    SCHEMA_VERSION,
    ReleaseError,
    _build_analytics,
    _build_catalog,
    _build_public_decision,
    _canonical_json_bytes,
    _csv_text,
    _default_global_caveats,
    _load_policies,
    _load_taxonomy,
    _privacy_scan_text,
    _slug_from_case_ref,
    _validate_against_schema,
    _write_canonical_json,
    _year_from_dates,
    scan_public_artifact,
)


def _iso_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value)


def _load_case_refs(conn: psycopg.Connection, decision_id: UUID | str) -> list[str]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT case_ref
            FROM decision_case_refs
            WHERE decision_id = %s
            ORDER BY ordinal, case_ref
            """,
            (decision_id,),
        )
        refs = [row["case_ref"] for row in cur.fetchall()]
    return refs


def _load_dates(conn: psycopg.Connection, decision_id: UUID | str) -> dict[str, str | None]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT date_type, date_value
            FROM decision_dates
            WHERE decision_id = %s
            """,
            (decision_id,),
        )
        rows = cur.fetchall()
    out: dict[str, str | None] = {
        "inquiry": None,
        "judgment": None,
        "publication": None,
        "conduct": None,
        "order_effective": None,
    }
    for row in rows:
        out[row["date_type"]] = _iso_date(row["date_value"])
    return out


def _load_decision_record(
    conn: psycopg.Connection,
    *,
    decision_id: UUID | str,
    selected_revision_ids: set[str] | None = None,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT d.*, r.code AS regulator_code, sc.source_id,
                   sc.max_excerpt_chars, sc.visibility, sc.attribution_required, sc.notes
            FROM decisions d
            JOIN regulators r ON r.id = d.regulator_id
            JOIN source_collections sc ON sc.id = d.source_collection_id
            WHERE d.id = %s
            """,
            (decision_id,),
        )
        decision = cur.fetchone()
        if decision is None:
            raise ReleaseError(f"Decision not found: {decision_id}")

        cur.execute(
            """
            SELECT DISTINCT ON (pr.extracted_proposition_id)
                pr.*,
                ep.client_ref,
                ep.confidence,
                (
                    SELECT rv.review_status
                    FROM reviews rv
                    WHERE rv.proposition_revision_id = pr.id
                    ORDER BY rv.created_at DESC
                    LIMIT 1
                ) AS review_status
            FROM proposition_revisions pr
            JOIN extracted_propositions ep ON ep.id = pr.extracted_proposition_id
            WHERE pr.decision_id = %s
            ORDER BY pr.extracted_proposition_id, pr.revision_number DESC
            """,
            (decision_id,),
        )
        revisions = list(cur.fetchall())

        cur.execute(
            """
            SELECT pe.extracted_proposition_id, pe.page_no, pe.quote_text,
                   pe.char_start, pe.char_end
            FROM proposition_evidence pe
            JOIN extracted_propositions ep ON ep.id = pe.extracted_proposition_id
            WHERE ep.decision_id = %s
            """,
            (decision_id,),
        )
        evidence_rows = list(cur.fetchall())

        cur.execute(
            """
            SELECT
                rel.relation_type,
                from_ep.client_ref AS from_ref,
                to_ep.client_ref AS to_ref
            FROM proposition_relations rel
            JOIN extracted_propositions from_ep ON from_ep.id = rel.from_proposition_id
            JOIN extracted_propositions to_ep ON to_ep.id = rel.to_proposition_id
            WHERE from_ep.decision_id = %s
            """,
            (decision_id,),
        )
        relations = [
            {
                "from_ref": row["from_ref"],
                "to_ref": row["to_ref"],
                "relation_type": row["relation_type"],
            }
            for row in cur.fetchall()
        ]

    evidence_by_prop: dict[str, list[dict[str, Any]]] = {}
    for ev in evidence_rows:
        key = str(ev["extracted_proposition_id"])
        evidence_by_prop.setdefault(key, []).append(
            {
                "page_no": ev["page_no"],
                "quote": ev["quote_text"],
                "quote_internal": ev["quote_text"],
                "char_start": ev["char_start"],
                "char_end": ev["char_end"],
            }
        )

    propositions: list[dict[str, Any]] = []
    for rev in revisions:
        if selected_revision_ids is not None and str(rev["id"]) not in selected_revision_ids:
            continue
        status = rev.get("review_status")
        published = status in {"accepted", "edited"}
        if not published:
            continue
        prop_id = str(rev["extracted_proposition_id"])
        structured = rev.get("structured_json")
        if isinstance(structured, str):
            structured = json.loads(structured)
        propositions.append(
            {
                "id": prop_id,
                "client_ref": rev["client_ref"],
                "prop_type": rev["prop_type"],
                "epistemic_class": rev["epistemic_class"],
                "derivation": rev["derivation"],
                "claim_text": rev["claim_text"],
                "structured": structured,
                "confidence": rev.get("confidence"),
                "review_status": status,
                "published": True,
                "evidence": evidence_by_prop.get(prop_id, []),
            }
        )

    case_refs = _load_case_refs(conn, decision_id)
    if not case_refs:
        case_refs = [decision["external_ref"]]

    coverage = decision.get("coverage_json") or {}
    if isinstance(coverage, str):
        coverage = json.loads(coverage)

    return {
        "id": str(decision["id"]),
        "regulator_code": decision["regulator_code"],
        "source_id": decision["source_id"],
        "fixture_kind": decision["fixture_kind"],
        "title": decision.get("title") or case_refs[0],
        "case_refs": case_refs,
        "case_ref": case_refs[0],
        "dates": _load_dates(conn, decision_id),
        "profession": decision["profession"],
        "defendant_name_as_published": decision.get("defendant_name_as_published"),
        "source_url": decision.get("official_source_url"),
        "official_source_url": decision.get("official_source_url"),
        "coverage": coverage,
        "relations": relations,
        "propositions": propositions,
        "external_ref": decision["external_ref"],
    }


def _annotation_for_release(ann: dict[str, Any]) -> dict[str, Any]:
    """Map DB annotation row to the shape expected by release._build_public_decision."""
    return {
        "external_ref": ann["external_ref"],
        "regulator_code": ann["regulator_code"],
        "issue_categories": list(ann.get("issue_categories") or []),
        "finding_outcomes": list(ann.get("finding_outcomes") or []),
        "sanction_categories": list(ann.get("sanction_categories") or []),
        "factor_categories": list(ann.get("factor_categories") or []),
        "editorial_note": {
            "summary": ann["summary"],
            "takeaway": ann["takeaway"],
            "supporting_client_refs": list(ann.get("supporting_client_refs") or []),
            "reviewer_status": ann["reviewer_status"],
        },
    }


def _load_annotation(
    conn: psycopg.Connection,
    *,
    decision_id: UUID | str,
    external_ref: str,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT * FROM editorial_annotations
            WHERE decision_id = %s OR external_ref = %s
            ORDER BY CASE WHEN decision_id = %s THEN 0 ELSE 1 END
            LIMIT 1
            """,
            (decision_id, external_ref, decision_id),
        )
        row = cur.fetchone()
    if row is None:
        raise ReleaseError(
            f"Missing editorial annotation for decision {decision_id} / {external_ref}"
        )
    return _annotation_for_release(dict(row))


def _policy_from_item(
    item: dict[str, Any], policies: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    source_id = item.get("source_id")
    if source_id and source_id in policies:
        return policies[source_id]
    # Fall back to live collection visibility for synthetic_demo path.
    return {
        "source_id": source_id,
        "visibility": item.get("visibility") or "internal_only",
        "max_excerpt_chars": item.get("max_excerpt_chars") or 280,
        "attribution_required": True,
        "notes": None,
    }


def build_release_from_postgres(
    conn: psycopg.Connection,
    *,
    publication_release_id: UUID | str,
    policy_path: Path,
    taxonomy_path: Path,
    output_dir: Path,
    released_at: str,
    selected_revision_ids: list[UUID | str] | None = None,
    title: str | None = None,
    description: str | None = None,
    mark_published: bool = True,
) -> dict[str, Any]:
    """
    Compile an approved (ready) Postgres release into the same artifact layout
    as `release.build_release`.
    """
    release = get_release(conn, publication_release_id=publication_release_id)
    if release is None:
        raise ReleaseRepoError(f"Unknown publication_release id={publication_release_id}")
    if release["status"] not in {APPROVED_STATUS, "building", "published"}:
        raise ReleaseRepoError(
            f"Release status={release['status']!r} is not approved for build "
            f"(expected {APPROVED_STATUS})"
        )

    release_mode = release["release_mode"]
    release_id = release["release_id"]
    if release_mode not in {"synthetic_demo", "public"}:
        raise ReleaseError(f"Invalid release_mode: {release_mode!r}")

    taxonomy = _load_taxonomy(taxonomy_path)
    policies = _load_policies(policy_path)
    selected_set = (
        {str(x) for x in selected_revision_ids} if selected_revision_ids is not None else None
    )

    items = list_release_items(conn, publication_release_id, included_only=True)
    if not items:
        raise ReleaseError("Release contains no included decisions")

    public_decisions: list[dict[str, Any]] = []

    ordered = sorted(items, key=lambda i: (i["public_slug"], str(i["decision_id"])))
    for item in ordered:
        decision = _load_decision_record(
            conn,
            decision_id=item["decision_id"],
            selected_revision_ids=selected_set,
        )
        annotation = _load_annotation(
            conn,
            decision_id=item["decision_id"],
            external_ref=item["external_ref"],
        )
        if annotation.get("regulator_code") != decision.get("regulator_code"):
            raise ReleaseError(
                f"Annotation regulator_code mismatch for {annotation.get('external_ref')}"
            )
        policy = _policy_from_item(item, policies)
        public_decisions.append(
            _build_public_decision(
                decision,
                release_id=release_id,
                release_mode=release_mode,
                annotation=annotation,
                policy=policy,
                taxonomy=taxonomy,
            )
        )

    if not public_decisions:
        raise ReleaseError("Release contains no publishable decisions")

    prop_count = sum(len(d["propositions"]) for d in public_decisions)
    regulators = sorted({d["regulator_code"] for d in public_decisions})

    release_title = (
        title
        or release.get("title")
        or (
            "RegLens HK synthetic demo release"
            if release_mode == "synthetic_demo"
            else "RegLens HK public release"
        )
    )
    release_description = (
        description
        or release.get("description")
        or ("Privacy-checked publication bundle for RegLens Observatory.")
    )
    corpus = release.get("corpus") or (
        "Synthetic MCHK/DCHK fixture decisions for Observatory demonstration."
        if release_mode == "synthetic_demo"
        else "Reviewed decisions from licensed/allowed public sources."
    )
    inclusion = release.get("inclusion_criteria") or (
        "Reviewed accepted/edited proposition revisions with editorial annotations."
    )
    exclusion = release.get("exclusion_criteria") or (
        "Pending/rejected propositions; raw page text; extractor metadata; model confidence."
    )
    caveats = list(release.get("global_caveats") or []) or _default_global_caveats(release_mode)

    catalog = _build_catalog(
        release_id=release_id, release_mode=release_mode, decisions=public_decisions
    )
    analytics = _build_analytics(
        release_id=release_id, release_mode=release_mode, decisions=public_decisions
    )

    if output_dir.exists():
        for child in sorted(output_dir.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
    decisions_dir = output_dir / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    file_records: list[dict[str, str]] = []
    for d in public_decisions:
        _validate_against_schema(d, "public_decision.v1.json")
        rel_path = f"decisions/{d['slug']}.json"
        digest = _write_canonical_json(output_dir / rel_path, d)
        file_records.append({"path": rel_path, "sha256": digest, "kind": "decision"})
        # Match slug back to decision id via case_refs[0]
        for item in ordered:
            if (
                item["public_slug"] == d["slug"]
                or _slug_from_case_ref(item["external_ref"]) == d["slug"]
            ):
                update_item_artifact_hash(
                    conn,
                    publication_release_id=publication_release_id,
                    decision_id=item["decision_id"],
                    artifact_sha256=digest,
                )
                break

    decision_headers = [
        "public_id",
        "slug",
        "regulator_code",
        "profession",
        "case_refs",
        "year",
        "issue_categories",
        "finding_outcomes",
        "sanction_categories",
        "factor_categories",
        "summary",
        "official_source_url",
    ]
    decision_rows: list[list[Any]] = []
    for d in public_decisions:
        decision_rows.append(
            [
                d["public_id"],
                d["slug"],
                d["regulator_code"],
                d["profession"],
                "|".join(d["case_refs"]),
                _year_from_dates(d.get("dates") or {}) or "",
                "|".join(d["issue_categories"]),
                "|".join(d["finding_outcomes"]),
                "|".join(d["sanction_categories"]),
                "|".join(d["factor_categories"]),
                d["editorial_takeaway"]["summary"],
                d["official_source_url"] or "",
            ]
        )
    decisions_csv = _csv_text(decision_headers, decision_rows)
    atomic_write_text(output_dir / "decisions.csv", decisions_csv)
    file_records.append(
        {
            "path": "decisions.csv",
            "sha256": sha256_bytes(decisions_csv.encode("utf-8")),
            "kind": "csv_decisions",
        }
    )

    prop_headers = [
        "public_id",
        "slug",
        "client_ref",
        "prop_type",
        "epistemic_class",
        "derivation",
        "verification_status",
        "claim_text",
        "evidence_pages",
    ]
    prop_rows: list[list[Any]] = []
    for d in public_decisions:
        for prop in d["propositions"]:
            pages = ",".join(str(e["page_no"]) for e in prop["evidence"])
            prop_rows.append(
                [
                    d["public_id"],
                    d["slug"],
                    prop["client_ref"],
                    prop["prop_type"],
                    prop["epistemic_class"],
                    prop["derivation"],
                    prop["verification_status"],
                    prop["claim_text"],
                    pages,
                ]
            )
    prop_rows.sort(key=lambda r: (r[1], r[2]))
    propositions_csv = _csv_text(prop_headers, prop_rows)
    atomic_write_text(output_dir / "propositions.csv", propositions_csv)
    file_records.append(
        {
            "path": "propositions.csv",
            "sha256": sha256_bytes(propositions_csv.encode("utf-8")),
            "kind": "csv_propositions",
        }
    )

    catalog_digest = _write_canonical_json(output_dir / "catalog.json", catalog)
    file_records.append({"path": "catalog.json", "sha256": catalog_digest, "kind": "catalog"})
    analytics_digest = _write_canonical_json(output_dir / "analytics.json", analytics)
    file_records.append({"path": "analytics.json", "sha256": analytics_digest, "kind": "analytics"})
    file_records.sort(key=lambda f: f["path"])

    generated_at = released_at
    release_manifest: dict[str, Any] = {
        "release_id": release_id,
        "schema_version": release.get("schema_version") or SCHEMA_VERSION,
        "release_mode": release_mode,
        "generated_at": generated_at,
        "released_at": released_at,
        "source_cutoff_date": _iso_date(release.get("source_cutoff_date")),
        "title": release_title,
        "description": release_description,
        "corpus": corpus,
        "regulators": regulators,
        "methodology_version": release.get("methodology_version") or METHODOLOGY_VERSION,
        "taxonomy_version": taxonomy["taxonomy_version"],
        "inclusion_criteria": inclusion,
        "exclusion_criteria": exclusion,
        "global_caveats": caveats,
        "decision_count": len(public_decisions),
        "proposition_count": prop_count,
        "files": file_records,
    }
    _validate_against_schema(release_manifest, "publication_release.v1.json")
    release_digest = _write_canonical_json(output_dir / "release.json", release_manifest)

    checksum_lines: list[str] = []
    all_files = [{"path": "release.json", "sha256": release_digest}] + file_records
    for rec in sorted(all_files, key=lambda f: f["path"]):
        checksum_lines.append(f"{rec['sha256']}  {rec['path']}")
    atomic_write_text(output_dir / "checksums.sha256", "\n".join(checksum_lines) + "\n")

    scan_hits = scan_public_artifact(output_dir)
    if scan_hits:
        raise ReleaseError("Public artifact privacy scan failed:\n" + "\n".join(scan_hits[:20]))

    # Final privacy sweep of manifest bytes (parity with decision builder)
    _privacy_scan_text(
        _canonical_json_bytes(release_manifest).decode("utf-8"),
        release_mode=release_mode,
        context="release.json",
    )

    if mark_published and release["status"] != "published":
        mark_release_published(
            conn,
            publication_release_id=publication_release_id,
            expected_version=int(release["version"]),
            manifest_sha256=release_digest,
            output_path=str(output_dir),
            decision_count=len(public_decisions),
            proposition_count=prop_count,
        )

    return release_manifest
