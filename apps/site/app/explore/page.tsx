"use client";

import Link from "next/link";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { DecisionCard } from "@/components/DecisionCard";
import { SearchForm } from "@/components/SearchForm";
import { SyntheticBanner } from "@/components/SyntheticBanner";
import {
  fetchCatalog,
  fetchRelease,
  matchesDecision,
  type Catalog,
  type CatalogDecision,
  type ReleaseMeta,
} from "@/lib/release";

function uniqueSorted(values: Array<string | null | undefined>): string[] {
  return Array.from(
    new Set(values.filter((v): v is string => Boolean(v))),
  ).sort();
}

function ExploreClient() {
  const searchParams = useSearchParams();
  const q = searchParams.get("q") || "";
  const regulator = searchParams.get("regulator") || "";
  const profession = searchParams.get("profession") || "";
  const issue = searchParams.get("issue") || "";
  const sanction = searchParams.get("sanction") || "";
  const year = searchParams.get("year") || "";

  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [release, setRelease] = useState<ReleaseMeta | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [compare, setCompare] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchCatalog(), fetchRelease()])
      .then(([c, r]) => {
        if (!cancelled) {
          setCatalog(c);
          setRelease(r);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered: CatalogDecision[] = useMemo(() => {
    if (!catalog) return [];
    return catalog.decisions.filter((d) =>
      matchesDecision(d, { q, regulator, profession, issue, sanction, year }),
    );
  }, [catalog, q, regulator, profession, issue, sanction, year]);

  const filterOptions = useMemo(() => {
    const decisions = catalog?.decisions || [];
    return {
      regulators: uniqueSorted(decisions.map((d) => d.regulator_code)),
      professions: uniqueSorted(decisions.map((d) => d.profession)),
      issues: uniqueSorted(decisions.flatMap((d) => d.issues || d.issue_categories || [])),
      sanctions: uniqueSorted(
        decisions.flatMap((d) => d.sanctions || d.sanction_categories || []),
      ),
      years: uniqueSorted(
        decisions.map((d) =>
          d.year != null
            ? String(d.year)
            : (d.decision_date || "").slice(0, 4) || null,
        ),
      ),
    };
  }, [catalog]);

  function toggleCompare(slug: string) {
    setCompare((prev) => {
      if (prev.includes(slug)) return prev.filter((s) => s !== slug);
      if (prev.length >= 4) return prev;
      return [...prev, slug];
    });
  }

  return (
    <>
      {release ? (
        <SyntheticBanner kind={release.kind} version={release.version} />
      ) : null}

      <header className="page-hero">
        <h1>Explore</h1>
        <p className="lede">
          Keyword and structured-field search across the release catalog. Filters
          sync to the URL. This is not FTS or semantic search.
        </p>
      </header>

      <section className="section">
        <SearchForm
          showFilters
          initialQ={q}
          initialRegulator={regulator}
          initialProfession={profession}
          initialIssue={issue}
          initialSanction={sanction}
          initialYear={year}
          regulators={filterOptions.regulators}
          professions={filterOptions.professions}
          issues={filterOptions.issues}
          sanctions={filterOptions.sanctions}
          years={filterOptions.years}
        />
      </section>

      {compare.length > 0 ? (
        <p>
          <Link className="btn" href={`/compare/?ids=${compare.join(",")}`}>
            Compare selected ({compare.length}/4)
          </Link>
        </p>
      ) : null}

      <section className="section" aria-live="polite">
        {error ? <p className="empty-state">Could not load catalog: {error}</p> : null}
        {!catalog && !error ? <p className="empty-state">Loading catalog…</p> : null}
        {catalog ? (
          <>
            <h2>
              {filtered.length} result{filtered.length === 1 ? "" : "s"}
            </h2>
            {filtered.length === 0 ? (
              <p className="empty-state">
                No decisions match these filters in the current release.
              </p>
            ) : (
              <ul className="decision-list">
                {filtered.map((d) => (
                  <li key={d.slug}>
                    <DecisionCard
                      decision={d}
                      selectable
                      selected={compare.includes(d.slug)}
                      onToggleSelect={toggleCompare}
                    />
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : null}
      </section>
    </>
  );
}

export default function ExplorePage() {
  return (
    <Suspense fallback={<p className="empty-state">Loading explore…</p>}>
      <ExploreClient />
    </Suspense>
  );
}
