"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type {
  ResearchDecisionSummary,
  ResearchExploreFilters,
  ResearchFacets,
} from "../../../lib/research-data";

type Props = {
  decisions: ResearchDecisionSummary[];
  facets: ResearchFacets;
  initialFilters: ResearchExploreFilters;
};

function matches(decision: ResearchDecisionSummary, filters: ResearchExploreFilters): boolean {
  const q = filters.q?.trim().toLowerCase();
  if (filters.regulator && decision.regulator_code !== filters.regulator) return false;
  if (filters.year && decision.year !== filters.year) return false;
  if (filters.issue && !decision.issue_categories.includes(filters.issue)) return false;
  if (
    filters.prop_type &&
    !decision.propositions.some((prop) => prop.prop_type === filters.prop_type)
  ) {
    return false;
  }
  if (!q) return true;
  const haystack = [
    decision.external_ref,
    decision.title,
    decision.summary,
    decision.takeaway,
    ...decision.propositions.map((prop) => prop.claim_text),
  ]
    .join(" ")
    .toLowerCase();
  return q
    .split(/\s+/)
    .filter(Boolean)
    .every((term) => haystack.includes(term));
}

function setParam(params: URLSearchParams, key: string, value?: string) {
  if (value?.trim()) {
    params.set(key, value.trim());
  } else {
    params.delete(key);
  }
}

export default function ExploreClient({ decisions, facets, initialFilters }: Props) {
  const router = useRouter();
  const [filters, setFilters] = useState<ResearchExploreFilters>(initialFilters);
  const results = useMemo(
    () => decisions.filter((decision) => matches(decision, filters)),
    [decisions, filters]
  );

  function updateFilter(key: keyof ResearchExploreFilters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const params = new URLSearchParams();
    setParam(params, "regulator", filters.regulator);
    setParam(params, "year", filters.year);
    setParam(params, "issue", filters.issue);
    setParam(params, "prop_type", filters.prop_type);
    setParam(params, "q", filters.q);
    router.push(`/research/explore${params.size ? `?${params.toString()}` : ""}`);
  }

  return (
    <>
      <form onSubmit={onSubmit} style={{ display: "grid", gap: "0.75rem", maxWidth: 760 }}>
        <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}>
          <select
            value={filters.regulator || ""}
            onChange={(event) => updateFilter("regulator", event.target.value)}
            aria-label="Filter by regulator"
          >
            <option value="">All regulators</option>
            {facets.regulators.map((regulator) => (
              <option key={regulator} value={regulator}>
                {regulator}
              </option>
            ))}
          </select>
          <select
            value={filters.year || ""}
            onChange={(event) => updateFilter("year", event.target.value)}
            aria-label="Filter by year"
          >
            <option value="">All years</option>
            {facets.years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
          <select
            value={filters.issue || ""}
            onChange={(event) => updateFilter("issue", event.target.value)}
            aria-label="Filter by issue"
          >
            <option value="">All issues</option>
            {facets.issues.map((issue) => (
              <option key={issue.code} value={issue.code}>
                {issue.label}
              </option>
            ))}
          </select>
          <select
            value={filters.prop_type || ""}
            onChange={(event) => updateFilter("prop_type", event.target.value)}
            aria-label="Filter by proposition type"
          >
            <option value="">All proposition types</option>
            {facets.prop_types.map((propType) => (
              <option key={propType} value={propType}>
                {propType}
              </option>
            ))}
          </select>
        </div>
        <input
          value={filters.q || ""}
          onChange={(event) => updateFilter("q", event.target.value)}
          placeholder="Keyword search across title, summary, takeaway, and propositions"
          style={{ padding: "0.55rem" }}
        />
        <div>
          <button type="submit">Apply URL filters</button>{" "}
          <button type="button" onClick={() => setFilters({})}>
            Clear
          </button>
        </div>
      </form>

      <p className="prop-type" style={{ marginTop: "1rem" }}>
        {results.length} result{results.length === 1 ? "" : "s"}
      </p>
      <div className="prop-list">
        {results.map((decision) => (
          <div className="prop" key={decision.external_ref}>
            <div className="prop-type">
              {decision.regulator_code} · {decision.year || "year unknown"} ·{" "}
              {decision.issue_categories.join(", ") || "no issue"}
            </div>
            <p className="claim">{decision.title || decision.external_ref}</p>
            <p>
              <strong>Charge:</strong>{" "}
              {decision.charge?.claim_text || "No reviewed charge proposition"}
            </p>
            <p>
              <strong>Finding:</strong>{" "}
              {decision.finding?.claim_text || decision.finding_outcomes.join(", ") || "No finding"}
            </p>
            <p>
              <strong>Sanction:</strong>{" "}
              {decision.sanction?.claim_text || decision.sanction_categories.join(", ") || "No sanction"}
            </p>
            <p style={{ color: "var(--muted)" }}>{decision.takeaway}</p>
            <Link href={`/research/compare?ids=${decision.id || decision.external_ref}`}>
              Compare
            </Link>
            {decision.id && (
              <>
                {" · "}
                <Link href={`/decisions/${decision.id}`}>Open decision</Link>
              </>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
