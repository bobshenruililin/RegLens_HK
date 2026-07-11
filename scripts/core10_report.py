#!/usr/bin/env python3
"""Generate synthetic-only Core10 readiness reports.

The report intentionally reads the checked public demo release, not private data
or Studio state. If the release contains real/public-mode decisions, generation
fails closed so the command cannot become a real-corpus export path.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RELEASE_DIR = ROOT / "generated" / "public-release"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "core10"
SYNTHETIC_LABEL = "SYNTHETIC DEMO ONLY - NOT REAL CORPUS"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _join(value: Any) -> str:
    return "|".join(_as_list(value))


def _md_cell(value: Any) -> str:
    text = str(value)
    return text.replace("|", "\\|")


def _load_decisions(release_dir: Path) -> list[dict[str, Any]]:
    catalog = _read_json(release_dir / "catalog.json")
    decisions: list[dict[str, Any]] = []
    for row in catalog.get("decisions", []):
        slug = row["slug"]
        detail_path = release_dir / "decisions" / f"{slug}.json"
        detail = _read_json(detail_path) if detail_path.exists() else {}
        decisions.append({**row, **detail})
    return decisions


def _assert_synthetic_only(release: dict[str, Any], decisions: list[dict[str, Any]]) -> None:
    release_mode = str(release.get("release_mode", ""))
    errors: list[str] = []
    if release_mode != "synthetic_demo":
        errors.append(f"release_mode is {release_mode!r}, expected 'synthetic_demo'")

    for decision in decisions:
        slug = str(decision.get("slug", "<missing-slug>"))
        fixture_kind = str(decision.get("fixture_kind", "synthetic"))
        decision_mode = str(decision.get("release_mode", release_mode))
        if fixture_kind != "synthetic":
            errors.append(f"{slug}: fixture_kind is {fixture_kind!r}, expected 'synthetic'")
        if decision_mode != "synthetic_demo":
            errors.append(f"{slug}: release_mode is {decision_mode!r}, expected 'synthetic_demo'")
        for prop in decision.get("propositions", []):
            status = str(prop.get("verification_status", ""))
            if status != "verified":
                client_ref = prop.get("client_ref", "<prop>")
                errors.append(f"{slug}/{client_ref}: not verified ({status!r})")

    if errors:
        joined = "\n - ".join(errors)
        raise SystemExit(
            "Refusing to generate Core10 report from non-synthetic or unreviewed data:\n"
            f" - {joined}"
        )


def _aggregate(decisions: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    by_regulator: Counter[str] = Counter()
    by_issue: Counter[str] = Counter()
    by_sanction: Counter[str] = Counter()
    by_prop_type: Counter[str] = Counter()

    for decision in decisions:
        by_regulator.update(_as_list(decision.get("regulator_code")))
        by_issue.update(_as_list(decision.get("issue_categories")))
        by_sanction.update(_as_list(decision.get("sanction_categories")))
        by_prop_type.update(
            str(prop.get("prop_type", "unknown")) for prop in decision.get("propositions", [])
        )

    return {
        "by_regulator": dict(sorted(by_regulator.items())),
        "by_issue_category": dict(sorted(by_issue.items())),
        "by_sanction_category": dict(sorted(by_sanction.items())),
        "by_prop_type": dict(sorted(by_prop_type.items())),
    }


def _decision_rows(decisions: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for decision in decisions:
        rows.append(
            {
                "synthetic_label": SYNTHETIC_LABEL,
                "slug": str(decision.get("slug", "")),
                "public_id": str(decision.get("public_id", "")),
                "regulator_code": str(decision.get("regulator_code", "")),
                "profession": str(decision.get("profession", "")),
                "year": "" if decision.get("year") is None else str(decision.get("year")),
                "issue_categories": _join(decision.get("issue_categories")),
                "finding_outcomes": _join(decision.get("finding_outcomes")),
                "sanction_categories": _join(decision.get("sanction_categories")),
                "factor_categories": _join(decision.get("factor_categories")),
                "proposition_count": str(len(decision.get("propositions", []))),
                "human_interpretation": "PLACEHOLDER - reviewer synthesis required",
            }
        )
    return rows


def _proposition_rows(decisions: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for decision in decisions:
        for prop in decision.get("propositions", []):
            rows.append(
                {
                    "synthetic_label": SYNTHETIC_LABEL,
                    "slug": str(decision.get("slug", "")),
                    "client_ref": str(prop.get("client_ref", "")),
                    "prop_type": str(prop.get("prop_type", "")),
                    "epistemic_class": str(prop.get("epistemic_class", "")),
                    "derivation": str(prop.get("derivation", "")),
                    "verification_status": str(prop.get("verification_status", "")),
                    "claim_text": str(prop.get("claim_text", "")),
                    "human_interpretation": (
                        "PLACEHOLDER - do not infer conclusions from counts alone"
                    ),
                }
            )
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(
    path: Path,
    *,
    release: dict[str, Any],
    decisions: list[dict[str, Any]],
    aggregate: dict[str, dict[str, int]],
) -> None:
    lines = [
        "# Core10 synthetic demo report",
        "",
        f"**Label:** {SYNTHETIC_LABEL}",
        "",
        "This report is generated from reviewed synthetic demo release data only.",
        "It is not a real Core10 result, not a statistical sample, and not legal advice.",
        "",
        "## Source release",
        "",
        f"- Release: `{release.get('release_id')}`",
        f"- Mode: `{release.get('release_mode')}`",
        f"- Generated at: `{release.get('generated_at')}`",
        f"- Observed decisions in demo release: {len(decisions)}",
        "- Target Core10 size: 10",
        "",
        "## Aggregate counts",
        "",
    ]
    for name, counts in aggregate.items():
        lines.append(f"### {name}")
        if counts:
            for key, count in counts.items():
                lines.append(f"- `{key}`: {count}")
        else:
            lines.append("- No values")
        lines.append("")

    lines.extend(
        [
            "## Decision rows",
            "",
            "| Slug | Regulator | Issues | Sanctions | Propositions |",
            "|------|-----------|--------|-----------|--------------|",
        ]
    )
    for decision in decisions:
        lines.append(
            "| {slug} | {regulator} | {issues} | {sanctions} | {count} |".format(
                slug=_md_cell(decision.get("slug", "")),
                regulator=_md_cell(decision.get("regulator_code", "")),
                issues=_md_cell(_join(decision.get("issue_categories")) or "-"),
                sanctions=_md_cell(_join(decision.get("sanction_categories")) or "-"),
                count=len(decision.get("propositions", [])),
            )
        )

    lines.extend(
        [
            "",
            "## Human interpretation placeholders",
            "",
            "- Reviewer synthesis: TODO after real Core10 internal review.",
            "- Coverage limitations: TODO after source selection is documented.",
            "- Uncertainty themes: TODO after reviewers code ambiguity.",
            "- Public-release decision: blocked until legal/source-policy approval.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def generate(release_dir: Path, output_dir: Path) -> None:
    release = _read_json(release_dir / "release.json")
    decisions = _load_decisions(release_dir)
    _assert_synthetic_only(release, decisions)

    aggregate = _aggregate(decisions)
    decision_rows = _decision_rows(decisions)
    proposition_rows = _proposition_rows(decisions)
    summary = {
        "schema_version": "1.0.0",
        "report_id": "core10.synthetic_demo",
        "label": SYNTHETIC_LABEL,
        "synthetic_only": True,
        "real_decisions_included": False,
        "release_id": release.get("release_id"),
        "release_mode": release.get("release_mode"),
        "release_generated_at": release.get("generated_at"),
        "target_decision_count": 10,
        "observed_decision_count": len(decisions),
        "observed_proposition_count": sum(len(d.get("propositions", [])) for d in decisions),
        "aggregate": aggregate,
        "human_interpretation": {
            "status": "placeholder",
            "notes": [
                "Reviewer synthesis required after real Core10 internal review.",
                "Do not infer prevalence or outcome rates from synthetic demo counts.",
                "Public real release remains blocked until legal/source-policy approval.",
            ],
        },
        "decisions": decision_rows,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "core10_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(output_dir / "core10_decisions.csv", decision_rows)
    _write_csv(output_dir / "core10_propositions.csv", proposition_rows)
    _write_markdown(
        output_dir / "core10_report.md",
        release=release,
        decisions=decisions,
        aggregate=aggregate,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-dir",
        type=Path,
        default=DEFAULT_RELEASE_DIR,
        help="Checked synthetic demo release directory (default: generated/public-release)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Report output directory (default: reports/core10)",
    )
    args = parser.parse_args()
    generate(args.release_dir, args.output_dir)


if __name__ == "__main__":
    main()
