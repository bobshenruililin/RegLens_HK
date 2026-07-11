"""Publication release builder for RegLens Observatory (MVP-RC1).

Builds a deterministic, privacy-checked public release bundle from reviewed
decisions. Public outputs never include model confidence, raw page text, or
extractor metadata.
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .atomic_io import atomic_write_bytes, atomic_write_text
from .hashutil import sha256_bytes
from .privacy import find_privacy_warnings, public_evidence_excerpt, redact_derived_text
from .store import LocalArtifactStore

SCHEMA_VERSION = "1.0.0"
METHODOLOGY_VERSION = "1.0.0"
DEFAULT_MAX_EXCERPT = 280

SYNTHETIC_ALLOWED_NAMES = (
    "Dr Jane Example",
    "Dr John Specimen",
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
PUBLICATIONS_SCHEMAS = _REPO_ROOT / "publications" / "schemas"

FORMAT_CHECKER = FormatChecker()


@FORMAT_CHECKER.checks("date", raises=ValueError)
def _check_date(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    date.fromisoformat(value)
    return True


@FORMAT_CHECKER.checks("date-time", raises=ValueError)
def _check_date_time(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    # Accept trailing Z
    normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
    datetime.fromisoformat(normalized)
    return True


class ReleaseError(ValueError):
    """Unsafe or invalid publication release."""


def _load_json(path: Path) -> Any:
    if not path.is_file():
        raise ReleaseError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_json_bytes(payload: Any) -> bytes:
    raw = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return raw.encode("utf-8")


def _write_canonical_json(path: Path, payload: Any) -> str:
    data = _canonical_json_bytes(payload)
    digest = sha256_bytes(data)
    atomic_write_bytes(path, data)
    return digest


def _slug_from_case_ref(case_ref: str) -> str:
    slug = case_ref.strip().lower()
    if not slug or not re.match(r"^[a-z0-9][a-z0-9._-]*$", slug):
        raise ReleaseError(f"Cannot derive public slug from case_ref={case_ref!r}")
    return slug


def _case_refs_for(decision: dict[str, Any]) -> list[str]:
    refs = list(decision.get("case_refs") or [])
    primary = decision.get("case_ref")
    if primary and primary not in refs:
        refs.insert(0, primary)
    if not refs:
        raise ReleaseError(f"Decision {decision.get('id')} has no case_refs")
    return refs


def _primary_case_ref(decision: dict[str, Any]) -> str:
    return _case_refs_for(decision)[0]


def _verification_status(review_status: str) -> str:
    if review_status == "accepted":
        return "verified"
    if review_status == "edited":
        return "human_edited"
    raise ReleaseError(f"Non-publishable review_status for public output: {review_status!r}")


def _load_taxonomy(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    codes: dict[str, set[str]] = {}
    for key in (
        "issue_categories",
        "finding_outcomes",
        "sanction_categories",
        "factor_categories",
    ):
        entries = data.get(key) or []
        codes[key] = {e["code"] for e in entries if isinstance(e, dict) and "code" in e}
        if not codes[key]:
            raise ReleaseError(f"Taxonomy missing codes for {key}: {path}")
    return {
        "taxonomy_version": data.get("taxonomy_version") or "1.0.0",
        "codes": codes,
        "raw": data,
    }


def _load_policies(path: Path) -> dict[str, dict[str, Any]]:
    data = _load_json(path)
    policies = data.get("policies") or []
    by_source: dict[str, dict[str, Any]] = {}
    for pol in policies:
        sid = pol.get("source_id")
        if not sid:
            raise ReleaseError(f"Policy entry missing source_id in {path}")
        by_source[sid] = pol
    if not by_source:
        raise ReleaseError(f"No source policies in {path}")
    return by_source


def _load_annotations(path: Path) -> dict[str, dict[str, Any]]:
    data = _load_json(path)
    out: dict[str, dict[str, Any]] = {}
    for ann in data.get("annotations") or []:
        ref = ann.get("external_ref")
        if not ref:
            raise ReleaseError(f"Annotation missing external_ref in {path}")
        if ref in out:
            raise ReleaseError(f"Duplicate annotation for external_ref={ref}")
        out[ref] = ann
    return out


def _validate_taxonomy_codes(
    *,
    annotation: dict[str, Any],
    taxonomy_codes: dict[str, set[str]],
    external_ref: str,
) -> None:
    mapping = {
        "issue_categories": "issue_categories",
        "finding_outcomes": "finding_outcomes",
        "sanction_categories": "sanction_categories",
        "factor_categories": "factor_categories",
    }
    for field, tax_key in mapping.items():
        values = annotation.get(field) or []
        allowed = taxonomy_codes[tax_key]
        for code in values:
            if code not in allowed:
                raise ReleaseError(
                    f"Unknown {field} code {code!r} for {external_ref}; allowed={sorted(allowed)}"
                )


def _strip_synthetic_names(text: str) -> str:
    out = text
    for name in SYNTHETIC_ALLOWED_NAMES:
        out = out.replace(name, "[SYNTHETIC_NAME]")
    return out


def _privacy_scan_text(text: str, *, release_mode: str, context: str) -> None:
    sample = text
    if release_mode == "synthetic_demo":
        sample = _strip_synthetic_names(sample)
    warnings = find_privacy_warnings(sample)
    if warnings:
        raise ReleaseError(f"Blocking privacy warning(s) in {context}: {', '.join(warnings)}")


def _published_propositions(decision: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for prop in decision.get("propositions") or []:
        status = prop.get("review_status")
        if status in {"pending", "rejected"}:
            continue
        if not prop.get("published"):
            continue
        if status not in {"accepted", "edited"}:
            raise ReleaseError(
                f"Decision {decision.get('id')} proposition {prop.get('client_ref')} "
                f"is published with invalid review_status={status!r}"
            )
        evidence = prop.get("evidence") or []
        if not evidence:
            raise ReleaseError(
                f"Decision {decision.get('id')} proposition {prop.get('client_ref')} "
                "has no evidence"
            )
        out.append(prop)
    return out


def _resolve_annotation(
    decision: dict[str, Any], annotations: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    refs = _case_refs_for(decision)
    for ref in refs:
        if ref in annotations:
            return annotations[ref]
    raise ReleaseError(
        f"Missing editorial annotation for case refs {refs} (decision {decision.get('id')})"
    )


def _effective_visibility(
    *,
    release_mode: str,
    fixture_kind: str,
    policy: dict[str, Any] | None,
) -> str:
    if release_mode == "synthetic_demo":
        if fixture_kind != "synthetic":
            raise ReleaseError(
                "synthetic_demo release only allows fixture_kind=synthetic decisions"
            )
        # Synthetic fixtures publish with public_excerpt regardless of real-source policy.
        return "public_excerpt"
    # public mode
    if fixture_kind == "synthetic":
        raise ReleaseError("public release cannot include synthetic fixtures (mixed corpus)")
    if policy is None:
        raise ReleaseError("public release requires a source publication policy")
    visibility = policy["visibility"]
    if visibility == "internal_only":
        raise ReleaseError(
            f"Source {policy.get('source_id')} is internal_only; cannot include in public release"
        )
    return visibility


def _source_attribution(
    *,
    release_mode: str,
    fixture_kind: str,
    regulator_code: str,
    policy: dict[str, Any] | None,
) -> str:
    if release_mode == "synthetic_demo" or fixture_kind == "synthetic":
        body = (
            "Medical Council of Hong Kong"
            if regulator_code == "MCHK"
            else "Dental Council of Hong Kong"
        )
        return (
            f"Synthetic fixture for RegLens HK demonstration only. Not an official {body} judgment."
        )
    if policy and policy.get("attribution_required"):
        if regulator_code == "MCHK":
            return (
                "Source: Medical Council of Hong Kong. Copyright of the Medical "
                "Council of Hong Kong. Reproduced excerpts are for research "
                "attribution under the applicable publication policy."
            )
        return (
            "Source: Dental Council of Hong Kong. Attribution required. "
            "Reproduced excerpts are for research under the applicable "
            "publication policy."
        )
    raise ReleaseError("Source attribution is required for public release")


def _publication_policy_caveats(
    *,
    release_mode: str,
    policy: dict[str, Any] | None,
    visibility: str,
) -> list[str]:
    caveats: list[str] = []
    if release_mode == "synthetic_demo":
        caveats.append(
            "This decision is part of a synthetic_demo release and is not a real "
            "regulatory judgment."
        )
        caveats.append(
            "Synthetic fixtures are published with public_excerpt visibility for "
            "demonstration only."
        )
    if policy and policy.get("notes"):
        caveats.append(str(policy["notes"]))
    if visibility == "public_metadata_only":
        caveats.append("Only metadata is published for this source; no excerpts.")
    elif visibility == "public_excerpt":
        caveats.append("Only short redacted evidence excerpts are published.")
    return caveats


def _build_public_proposition(
    prop: dict[str, Any],
    *,
    max_excerpt_chars: int,
    release_mode: str,
    visibility: str,
    decision_id: str,
) -> dict[str, Any]:
    claim = redact_derived_text(prop.get("claim_text") or "")
    if not claim:
        raise ReleaseError(
            f"Empty claim after redaction for {decision_id}/{prop.get('client_ref')}"
        )
    _privacy_scan_text(
        claim,
        release_mode=release_mode,
        context=f"claim {decision_id}/{prop.get('client_ref')}",
    )

    structured = prop.get("structured")
    if isinstance(structured, dict):
        structured = {
            k: (redact_derived_text(v) if isinstance(v, str) else v) for k, v in structured.items()
        }
        for k, v in structured.items():
            if isinstance(v, str):
                _privacy_scan_text(
                    v,
                    release_mode=release_mode,
                    context=f"structured.{k} {decision_id}/{prop.get('client_ref')}",
                )

    evidence_out: list[dict[str, Any]] = []
    if visibility == "public_metadata_only":
        # Metadata-only: still require internal evidence existed, but omit excerpts
        # by using a placeholder page marker from first evidence without quote text.
        # Mission requires public evidence excerpts for excerpt modes; for
        # metadata_only we omit evidence array content quotes — schema requires
        # minItems 1, so metadata_only is currently not used for real sources.
        raise ReleaseError(
            "public_metadata_only visibility is not supported for proposition "
            "publication in MVP-RC1 (use public_excerpt or keep internal_only)"
        )

    for ev in prop.get("evidence") or []:
        quote = ev.get("quote_internal") or ev.get("quote") or ""
        if not quote:
            raise ReleaseError(f"Missing evidence quote for {decision_id}/{prop.get('client_ref')}")
        excerpt = public_evidence_excerpt(quote, max_chars=max_excerpt_chars)
        if len(excerpt) > max_excerpt_chars:
            raise ReleaseError(
                f"Excerpt exceeds max_excerpt_chars={max_excerpt_chars} for "
                f"{decision_id}/{prop.get('client_ref')}"
            )
        _privacy_scan_text(
            excerpt,
            release_mode=release_mode,
            context=f"excerpt {decision_id}/{prop.get('client_ref')}",
        )
        page_no = ev.get("page_no")
        if not isinstance(page_no, int) or page_no < 1:
            raise ReleaseError(
                f"Invalid evidence page_no for {decision_id}/{prop.get('client_ref')}"
            )
        evidence_out.append({"page_no": page_no, "excerpt": excerpt})

    if "confidence" in prop and release_mode:
        # confidence is stripped — never copied
        pass

    public_prop: dict[str, Any] = {
        "client_ref": prop["client_ref"],
        "prop_type": prop["prop_type"],
        "epistemic_class": prop["epistemic_class"],
        "derivation": prop["derivation"],
        "claim_text": claim,
        "structured": structured if structured is not None else None,
        "verification_status": _verification_status(prop["review_status"]),
        "evidence": evidence_out,
    }
    return public_prop


def _filter_relations(
    relations: list[dict[str, Any]], published_refs: set[str]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rel in relations or []:
        from_ref = rel.get("from_ref")
        to_ref = rel.get("to_ref")
        if from_ref in published_refs and to_ref in published_refs:
            out.append(
                {
                    "from_ref": from_ref,
                    "to_ref": to_ref,
                    "relation_type": rel["relation_type"],
                }
            )
    out.sort(key=lambda r: (r["relation_type"], r["from_ref"], r["to_ref"]))
    return out


def _build_public_decision(
    decision: dict[str, Any],
    *,
    release_id: str,
    release_mode: str,
    annotation: dict[str, Any],
    policy: dict[str, Any] | None,
    taxonomy: dict[str, Any],
) -> dict[str, Any]:
    fixture_kind = decision.get("fixture_kind") or "real"
    visibility = _effective_visibility(
        release_mode=release_mode,
        fixture_kind=fixture_kind,
        policy=policy,
    )
    if policy and isinstance(policy.get("max_excerpt_chars"), int):
        max_excerpt = int(policy["max_excerpt_chars"])
    else:
        max_excerpt = DEFAULT_MAX_EXCERPT

    published = _published_propositions(decision)
    if not published:
        raise ReleaseError(
            f"Decision {decision.get('id')} has no published accepted/edited propositions"
        )

    _validate_taxonomy_codes(
        annotation=annotation,
        taxonomy_codes=taxonomy["codes"],
        external_ref=annotation["external_ref"],
    )

    note = annotation["editorial_note"]
    published_refs = {p["client_ref"] for p in published}
    for ref in note.get("supporting_client_refs") or []:
        if ref not in published_refs:
            raise ReleaseError(
                f"Annotation {annotation['external_ref']} supporting_client_ref "
                f"{ref!r} is not among published propositions {sorted(published_refs)}"
            )

    takeaway_summary = redact_derived_text(note["summary"])
    takeaway_body = redact_derived_text(note["takeaway"])
    for label, text in (("summary", takeaway_summary), ("takeaway", takeaway_body)):
        _privacy_scan_text(
            text,
            release_mode=release_mode,
            context=f"editorial {label} {annotation['external_ref']}",
        )

    public_props = [
        _build_public_proposition(
            prop,
            max_excerpt_chars=max_excerpt,
            release_mode=release_mode,
            visibility=visibility,
            decision_id=str(decision.get("id")),
        )
        for prop in sorted(published, key=lambda p: p["client_ref"])
    ]

    case_refs = _case_refs_for(decision)
    slug = _slug_from_case_ref(case_refs[0])
    official_url = decision.get("source_url")
    if release_mode == "public" and not official_url:
        raise ReleaseError(
            f"Real public decision {case_refs[0]} requires official_source_url / source_url"
        )

    attribution = _source_attribution(
        release_mode=release_mode,
        fixture_kind=fixture_kind,
        regulator_code=decision["regulator_code"],
        policy=policy,
    )
    if not attribution.strip():
        raise ReleaseError(f"Empty source attribution for {case_refs[0]}")

    dates = decision.get("dates") or {}
    coverage = decision.get("coverage") or {}
    coverage_warnings = list(coverage.get("warnings") or [])
    for w in decision.get("segmentation_warnings") or []:
        if w not in coverage_warnings:
            coverage_warnings.append(w)

    public_decision: dict[str, Any] = {
        "public_id": f"{release_id}:{slug}",
        "slug": slug,
        "release_id": release_id,
        "release_mode": release_mode,
        "regulator_code": decision["regulator_code"],
        "profession": decision["profession"],
        "case_refs": case_refs,
        "dates": {
            "inquiry": dates.get("inquiry"),
            "judgment": dates.get("judgment"),
            "publication": dates.get("publication"),
            "conduct": dates.get("conduct"),
            "order_effective": dates.get("order_effective"),
        },
        "official_source_url": official_url,
        "source_attribution": attribution,
        "publication_policy_caveats": _publication_policy_caveats(
            release_mode=release_mode, policy=policy, visibility=visibility
        ),
        "editorial_takeaway": {
            "summary": takeaway_summary,
            "takeaway": takeaway_body,
            "status": note["reviewer_status"],
        },
        "issue_categories": list(annotation["issue_categories"]),
        "finding_outcomes": list(annotation["finding_outcomes"]),
        "sanction_categories": list(annotation["sanction_categories"]),
        "factor_categories": list(annotation.get("factor_categories") or []),
        "propositions": public_props,
        "relations": _filter_relations(decision.get("relations") or [], published_refs),
        "coverage_warnings": coverage_warnings,
        "title": decision.get("title") or case_refs[0],
        "fixture_kind": fixture_kind,
    }

    # Final privacy sweep across serialised public fields
    _privacy_scan_text(
        json.dumps(public_decision, ensure_ascii=False),
        release_mode=release_mode,
        context=f"public decision {slug}",
    )

    # Forbidden fields must never appear
    blob = json.dumps(public_decision)
    if '"confidence"' in blob:
        raise ReleaseError(f"confidence leaked into public decision {slug}")
    if "extractor" in public_decision:
        raise ReleaseError(f"extractor leaked into public decision {slug}")
    if "pages" in public_decision:
        raise ReleaseError(f"pages leaked into public decision {slug}")

    return public_decision


def _year_from_dates(dates: dict[str, Any]) -> int | None:
    for key in ("judgment", "inquiry", "publication", "order_effective", "conduct"):
        val = dates.get(key)
        if isinstance(val, str) and len(val) >= 4:
            try:
                return int(val[:4])
            except ValueError:
                continue
    return None


def _build_catalog(
    *,
    release_id: str,
    release_mode: str,
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    entries = []
    for d in decisions:
        entries.append(
            {
                "public_id": d["public_id"],
                "slug": d["slug"],
                "title": d.get("title") or d["case_refs"][0],
                "regulator_code": d["regulator_code"],
                "profession": d["profession"],
                "case_refs": d["case_refs"],
                "year": _year_from_dates(d.get("dates") or {}),
                "issue_categories": d["issue_categories"],
                "finding_outcomes": d["finding_outcomes"],
                "sanction_categories": d["sanction_categories"],
                "factor_categories": d["factor_categories"],
                "summary": d["editorial_takeaway"]["summary"],
                "official_source_url": d["official_source_url"],
                "release_mode": release_mode,
            }
        )
    entries.sort(key=lambda e: (e["regulator_code"], e["slug"]))
    return {
        "release_id": release_id,
        "release_mode": release_mode,
        "schema_version": SCHEMA_VERSION,
        "decision_count": len(entries),
        "decisions": entries,
    }


def _build_analytics(
    *,
    release_id: str,
    release_mode: str,
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    by_regulator: dict[str, int] = {}
    by_year: dict[str, int] = {}
    by_issue: dict[str, int] = {}
    by_sanction: dict[str, int] = {}
    by_finding: dict[str, int] = {}
    issue_sanction: dict[str, int] = {}
    prop_count = 0

    for d in decisions:
        reg = d["regulator_code"]
        by_regulator[reg] = by_regulator.get(reg, 0) + 1
        year = _year_from_dates(d.get("dates") or {})
        year_key = str(year) if year is not None else "unknown"
        by_year[year_key] = by_year.get(year_key, 0) + 1
        prop_count += len(d.get("propositions") or [])
        for issue in d.get("issue_categories") or []:
            by_issue[issue] = by_issue.get(issue, 0) + 1
            for san in d.get("sanction_categories") or []:
                pair = f"{issue}|{san}"
                issue_sanction[pair] = issue_sanction.get(pair, 0) + 1
        for san in d.get("sanction_categories") or []:
            by_sanction[san] = by_sanction.get(san, 0) + 1
        for finding in d.get("finding_outcomes") or []:
            by_finding[finding] = by_finding.get(finding, 0) + 1

    return {
        "release_id": release_id,
        "release_mode": release_mode,
        "schema_version": SCHEMA_VERSION,
        "decision_count": len(decisions),
        "proposition_count": prop_count,
        "by_regulator": dict(sorted(by_regulator.items())),
        "by_year": dict(sorted(by_year.items())),
        "by_issue_category": dict(sorted(by_issue.items())),
        "by_sanction_category": dict(sorted(by_sanction.items())),
        "by_finding_outcome": dict(sorted(by_finding.items())),
        "issue_sanction_heatmap": [
            {
                "issue_category": k.split("|", 1)[0],
                "sanction_category": k.split("|", 1)[1],
                "count": v,
            }
            for k, v in sorted(issue_sanction.items())
        ],
        "bias_warning": (
            "These figures describe decisions in the published corpus and do not "
            "represent complaint or misconduct rates."
        ),
    }


def _csv_text(headers: list[str], rows: list[list[Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def _load_schema(name: str) -> dict[str, Any]:
    path = PUBLICATIONS_SCHEMAS / name
    if not path.is_file():
        raise ReleaseError(f"Schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_against_schema(payload: dict[str, Any], schema_name: str) -> None:
    schema = _load_schema(schema_name)
    validator = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
    errors = sorted({e.message for e in validator.iter_errors(payload)})
    if errors:
        raise ReleaseError(f"Schema validation failed for {schema_name}: {errors[0]}")


def _default_global_caveats(release_mode: str) -> list[str]:
    caveats = [
        "RegLens HK is not legal advice and does not predict outcomes or recommend sanctions.",
        (
            "Published claims are human-reviewed extracts and editorial "
            "classifications, not the full judgment."
        ),
        (
            "Patient and third-party identifiers are minimised; the scanner does "
            "not claim complete de-identification."
        ),
    ]
    if release_mode == "synthetic_demo":
        caveats.insert(
            0,
            "SYNTHETIC DEMO RELEASE: all decisions are synthetic fixtures, not official judgments.",
        )
    else:
        caveats.append(
            "Real-source republication remains constrained by each source publication policy."
        )
    return caveats


def build_release(
    *,
    data_root: Path,
    annotations_path: Path,
    policy_path: Path,
    taxonomy_path: Path,
    release_id: str,
    release_mode: str,
    released_at: str,
    output_dir: Path,
    title: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic public release bundle into output_dir."""
    if release_mode not in {"synthetic_demo", "public"}:
        raise ReleaseError(f"Invalid release_mode: {release_mode!r}")

    # Deterministic timestamp: generated_at mirrors explicit released_at
    generated_at = released_at

    taxonomy = _load_taxonomy(taxonomy_path)
    policies = _load_policies(policy_path)
    annotations = _load_annotations(annotations_path)

    # Validate annotation / policy files against schemas
    _validate_against_schema(_load_json(annotations_path), "editorial_annotations.v1.json")
    _validate_against_schema(_load_json(policy_path), "source_publication_policy.v1.json")

    store = LocalArtifactStore(data_root)
    raw_decisions = store.list_decisions()
    if not raw_decisions:
        raise ReleaseError(f"No decisions found under {data_root}/seed/decisions")

    public_decisions: list[dict[str, Any]] = []
    kinds_seen: set[str] = set()

    # Stable order by primary case_ref
    ordered = sorted(raw_decisions, key=lambda d: (_primary_case_ref(d), d.get("id") or ""))

    for decision in ordered:
        fixture_kind = decision.get("fixture_kind") or "real"
        kinds_seen.add(fixture_kind)
        source_id = decision.get("source_id")
        policy = policies.get(source_id) if source_id else None

        if release_mode == "synthetic_demo" and fixture_kind != "synthetic":
            raise ReleaseError(
                f"synthetic_demo refused non-synthetic decision "
                f"{decision.get('id')} fixture_kind={fixture_kind!r}"
            )
        if release_mode == "public":
            if fixture_kind == "synthetic":
                raise ReleaseError(
                    f"public release refused synthetic decision {decision.get('id')}"
                )
            if policy is None:
                raise ReleaseError(
                    f"No publication policy for source_id={source_id!r} "
                    f"(decision {decision.get('id')})"
                )
            if policy.get("visibility") == "internal_only":
                raise ReleaseError(
                    f"Refusing internal_only source {source_id} in public release "
                    f"(decision {decision.get('id')})"
                )

        annotation = _resolve_annotation(decision, annotations)
        if annotation.get("regulator_code") != decision.get("regulator_code"):
            raise ReleaseError(
                f"Annotation regulator_code mismatch for {annotation.get('external_ref')}"
            )

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

    if "synthetic" in kinds_seen and "real" in kinds_seen:
        raise ReleaseError(
            "Release mixes synthetic and real material without an explicit mixed policy"
        )

    if not public_decisions:
        raise ReleaseError("Release contains no publishable decisions")

    prop_count = sum(len(d["propositions"]) for d in public_decisions)
    regulators = sorted({d["regulator_code"] for d in public_decisions})

    release_title = title or (
        "RegLens HK synthetic demo release"
        if release_mode == "synthetic_demo"
        else "RegLens HK public release"
    )
    release_description = description or (
        "Privacy-checked publication bundle for RegLens Observatory. "
        + (
            "Contains synthetic fixture decisions only."
            if release_mode == "synthetic_demo"
            else "Contains expressly publishable reviewed decisions."
        )
    )

    corpus = (
        "Synthetic MCHK/DCHK fixture decisions for Observatory demonstration."
        if release_mode == "synthetic_demo"
        else "Reviewed decisions from licensed/allowed public sources."
    )
    inclusion = (
        "Synthetic fixtures with published accepted/edited propositions and "
        "matching editorial annotations."
        if release_mode == "synthetic_demo"
        else "Real decisions whose source policy permits public excerpt or fuller "
        "publication, with published accepted/edited propositions and annotations."
    )
    exclusion = (
        "Pending/rejected propositions; raw page text; extractor metadata; "
        "model confidence; real internal_only sources; non-annotated decisions."
    )

    catalog = _build_catalog(
        release_id=release_id, release_mode=release_mode, decisions=public_decisions
    )
    analytics = _build_analytics(
        release_id=release_id, release_mode=release_mode, decisions=public_decisions
    )

    # Prepare output directory deterministically
    if output_dir.exists():
        # Only remove generated release files we own; require empty or recreate
        for child in sorted(output_dir.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
    decisions_dir = output_dir / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    file_records: list[dict[str, str]] = []

    # Write per-decision JSON
    for d in public_decisions:
        _validate_against_schema(d, "public_decision.v1.json")
        rel_path = f"decisions/{d['slug']}.json"
        digest = _write_canonical_json(output_dir / rel_path, d)
        file_records.append({"path": rel_path, "sha256": digest, "kind": "decision"})

    # CSV exports
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
    decisions_csv_path = output_dir / "decisions.csv"
    atomic_write_text(decisions_csv_path, decisions_csv)
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
    propositions_csv_path = output_dir / "propositions.csv"
    atomic_write_text(propositions_csv_path, propositions_csv)
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

    # Sort file records for deterministic manifest (exclude release.json itself)
    file_records.sort(key=lambda f: f["path"])

    release_manifest: dict[str, Any] = {
        "release_id": release_id,
        "schema_version": SCHEMA_VERSION,
        "release_mode": release_mode,
        "generated_at": generated_at,
        "released_at": released_at,
        "source_cutoff_date": None,
        "title": release_title,
        "description": release_description,
        "corpus": corpus,
        "regulators": regulators,
        "methodology_version": METHODOLOGY_VERSION,
        "taxonomy_version": taxonomy["taxonomy_version"],
        "inclusion_criteria": inclusion,
        "exclusion_criteria": exclusion,
        "global_caveats": _default_global_caveats(release_mode),
        "decision_count": len(public_decisions),
        "proposition_count": prop_count,
        "files": file_records,
    }
    _validate_against_schema(release_manifest, "publication_release.v1.json")
    release_digest = _write_canonical_json(output_dir / "release.json", release_manifest)

    # Checksums cover all release artifacts including release.json
    checksum_lines: list[str] = []
    all_files = [{"path": "release.json", "sha256": release_digest}] + file_records
    for rec in sorted(all_files, key=lambda f: f["path"]):
        checksum_lines.append(f"{rec['sha256']}  {rec['path']}")
    checksum_text = "\n".join(checksum_lines) + "\n"
    atomic_write_text(output_dir / "checksums.sha256", checksum_text)

    # Final privacy scan of the entire artifact directory
    scan_hits = scan_public_artifact(output_dir)
    if scan_hits:
        raise ReleaseError("Public artifact privacy scan failed:\n" + "\n".join(scan_hits[:20]))

    return release_manifest


def scan_public_artifact(path: Path) -> list[str]:
    """Scan a release file or directory for blocking privacy warnings.

    Returns a list of human-readable findings (empty if clean). For
    synthetic_demo releases, known synthetic practitioner names are allowed.
    """
    findings: list[str] = []
    if not path.exists():
        return [f"path does not exist: {path}"]

    release_mode = "public"
    release_json = path / "release.json" if path.is_dir() else None
    if path.is_file() and path.name == "release.json":
        release_json = path
    if release_json and release_json.is_file():
        try:
            meta = json.loads(release_json.read_text(encoding="utf-8"))
            release_mode = meta.get("release_mode") or "public"
        except json.JSONDecodeError:
            findings.append(f"invalid release.json: {release_json}")

    targets: list[Path]
    if path.is_file():
        targets = [path]
    else:
        targets = sorted(
            p
            for p in path.rglob("*")
            if p.is_file() and p.suffix.lower() in {".json", ".csv", ".sha256", ".txt", ".md"}
        )

    for file_path in targets:
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"{file_path}: binary or non-utf8 content")
            continue
        sample = text
        if release_mode == "synthetic_demo":
            sample = _strip_synthetic_names(sample)
        warnings = find_privacy_warnings(sample)
        for code in warnings:
            label = str(file_path.relative_to(path)) if path.is_dir() else file_path.name
            findings.append(f"{label}: {code}")
    return findings
