import Link from "next/link";
import { SearchForm } from "@/components/SearchForm";
import { SyntheticBanner } from "@/components/SyntheticBanner";
import {
  exploreHref,
  loadAnalytics,
  loadCatalog,
  loadRelease,
} from "@/lib/release";

export default function HomePage() {
  const release = loadRelease();
  const catalog = loadCatalog();
  const analytics = loadAnalytics();
  const yearRows = analytics.year_rows || [];
  const regulators = new Set(catalog.decisions.map((d) => d.regulator_code));
  const yearMax = Math.max(...yearRows.map((y) => y.count), 1);

  return (
    <>
      <SyntheticBanner kind={release.kind} version={release.version} />

      <header className="page-hero">
        <span className="brand-mark">RegLens Observatory</span>
        <h1>Structured disciplinary research, read-only</h1>
        <p className="lede">
          Explore published MCHK and DCHK decision extracts with keyword and
          structured-field search. This site does not offer full-text search
          engines or semantic retrieval.
        </p>
      </header>

      <section className="section" aria-labelledby="search-heading">
        <h2 id="search-heading">Search the corpus</h2>
        <p>
          Match keywords against titles, case references, issues, sanctions, and
          other structured fields.
        </p>
        <SearchForm />
        <p className="meta-row" style={{ marginTop: "0.75rem" }}>
          Example queries:{" "}
          <Link href={exploreHref({ q: "recordkeeping" })}>recordkeeping</Link>
          {" · "}
          <Link href={exploreHref({ q: "warning", regulator: "MCHK" })}>
            MCHK warning
          </Link>
          {" · "}
          <Link href={exploreHref({ issue: "premises_equipment" })}>
            premises equipment
          </Link>
        </p>
      </section>

      <section className="section" aria-labelledby="counts-heading">
        <h2 id="counts-heading">Release snapshot</h2>
        <ul className="counts">
          <li>
            <span className="label">Decisions</span>
            <span className="value">{release.decision_count}</span>
          </li>
          <li>
            <span className="label">Propositions</span>
            <span className="value">{release.proposition_count}</span>
          </li>
          <li>
            <span className="label">Regulators</span>
            <span className="value">
              {regulators.size ||
                (Array.isArray(release.regulators)
                  ? release.regulators.length
                  : 0)}
            </span>
          </li>
          <li>
            <span className="label">Release</span>
            <span className="value" style={{ fontSize: "1.15rem" }}>
              {release.version}
            </span>
          </li>
        </ul>
      </section>

      <section className="section" aria-labelledby="bias-heading">
        <h2 id="bias-heading">Coverage and bias warning</h2>
        <p>
          Observed counts reflect only decisions present in this release. Missing
          years, under-reported issue types, and synthetic fixtures can skew
          charts. Do not treat distributions as population rates or outcome
          predictions.
        </p>
        <div className="link-row">
          <Link className="btn btn--ghost" href="/methodology/">
            Read methodology
          </Link>
          <Link className="btn btn--ghost" href="/analytics/">
            View analytics
          </Link>
        </div>
      </section>

      <section className="section" aria-labelledby="timeline-heading">
        <h2 id="timeline-heading">Decisions by year</h2>
        <p>Timeline of decision counts in the current release.</p>
        {yearRows.length === 0 ? (
          <p className="empty-state">No yearly aggregates in this release.</p>
        ) : (
          <div className="timeline" role="list">
            {yearRows.map((row) => {
              const pct = Math.round((row.count / yearMax) * 100);
              return (
                <div
                  className="timeline__row"
                  role="listitem"
                  key={String(row.year)}
                >
                  <div className="timeline__year">
                    <Link href={exploreHref({ year: String(row.year) })}>
                      {row.year}
                    </Link>
                  </div>
                  <div
                    className="timeline__track"
                    title={`${row.count} decisions`}
                    aria-label={`${row.year}: ${row.count} decisions`}
                  >
                    <div
                      className="timeline__fill"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="section" aria-labelledby="links-heading">
        <h2 id="links-heading">Continue</h2>
        <div className="link-row">
          <Link className="btn" href="/explore/">
            Explore decisions
          </Link>
          <Link className="btn btn--ghost" href="/compare/">
            Compare
          </Link>
          <Link className="btn btn--ghost" href="/data/">
            Download release
          </Link>
        </div>
      </section>
    </>
  );
}
