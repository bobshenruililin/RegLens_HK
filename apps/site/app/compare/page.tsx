"use client";

import Link from "next/link";
import {
  Suspense,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { SyntheticBanner } from "@/components/SyntheticBanner";
import {
  fetchCatalog,
  fetchRelease,
  type Catalog,
  type CatalogDecision,
  type ReleaseMeta,
} from "@/lib/release";

function parseIds(raw: string | null): string[] {
  if (!raw) return [];
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 4);
}

function CompareClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const ids = useMemo(
    () => parseIds(searchParams.get("ids")),
    [searchParams],
  );

  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [release, setRelease] = useState<ReleaseMeta | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState(ids.join(","));

  useEffect(() => {
    setDraft(ids.join(","));
  }, [ids]);

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

  const selected: CatalogDecision[] = useMemo(() => {
    if (!catalog) return [];
    return ids
      .map((slug) => catalog.decisions.find((d) => d.slug === slug))
      .filter((d): d is CatalogDecision => Boolean(d));
  }, [catalog, ids]);

  function applyIds(e: FormEvent) {
    e.preventDefault();
    const next = parseIds(draft).join(",");
    router.push(next ? `/compare/?ids=${encodeURIComponent(next)}` : "/compare/");
  }

  return (
    <>
      {release ? (
        <SyntheticBanner kind={release.kind} version={release.version} />
      ) : null}

      <header className="page-hero">
        <h1>Compare</h1>
        <p className="lede">
          Compare up to four decisions side by side. Pass slugs in the{" "}
          <code>ids</code> query parameter (comma-separated).
        </p>
      </header>

      <form className="search-form" onSubmit={applyIds}>
        <label htmlFor="compare-ids">Decision slugs (max 4)</label>
        <div className="search-form__row">
          <input
            id="compare-ids"
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="slug-a,slug-b"
            autoComplete="off"
          />
          <button className="btn" type="submit">
            Update
          </button>
        </div>
      </form>

      {error ? <p className="empty-state">Could not load catalog: {error}</p> : null}

      {!catalog && !error ? (
        <p className="empty-state">Loading…</p>
      ) : null}

      {catalog && ids.length === 0 ? (
        <p className="empty-state">
          No decisions selected.{" "}
          <Link href="/explore/">Explore the catalog</Link> and choose up to four.
        </p>
      ) : null}

      {selected.length > 0 ? (
        <div className="compare-grid" style={{ marginTop: "2rem" }}>
          {selected.map((d) => (
            <article key={d.slug} className="compare-col">
              <h3>
                <Link href={`/decisions/${d.slug}/`}>{d.title}</Link>
              </h3>
              <dl className="detail-dl" style={{ gridTemplateColumns: "1fr" }}>
                <dt>Regulator</dt>
                <dd>{d.regulator_code}</dd>
                <dt>Date</dt>
                <dd>{d.decision_date || "—"}</dd>
                <dt>Profession</dt>
                <dd>{d.profession || "—"}</dd>
                <dt>Case ref</dt>
                <dd>{d.case_ref || "—"}</dd>
                <dt>Issues</dt>
                <dd>{(d.issues || []).length ? (d.issues || []).join("; ") : "—"}</dd>
                <dt>Sanctions</dt>
                <dd>
                  {(d.sanctions || []).length
                    ? (d.sanctions || []).join("; ")
                    : "—"}
                </dd>
              </dl>
              {d.summary ? <p>{d.summary}</p> : null}
            </article>
          ))}
        </div>
      ) : null}

      {catalog && ids.length > 0 && selected.length < ids.length ? (
        <p className="empty-state">
          Some requested slugs were not found in this release.
        </p>
      ) : null}
    </>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<p className="empty-state">Loading compare…</p>}>
      <CompareClient />
    </Suspense>
  );
}
