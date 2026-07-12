import Link from "next/link";
import { StatusNotice } from "@/components/StatusNotice";
import { SearchList } from "@/components/SearchList";
import { loadRootManifest, loadSections } from "@/lib/data";
import {
  HERO_HEADING,
  HERO_SUBHEADING,
  PRODUCT_PROMISE,
} from "@/lib/disclaimer";
import { relationshipLabel } from "@/lib/format";
import { instrumentCompletenessBadge } from "@/lib/mode";

export default function HomePage() {
  const root = loadRootManifest();
  const example = root.instruments.find((i) => i.available)?.example_comparison;
  const exampleSlug = example
    ? example.instrument_id.replace(":", "-").toLowerCase()
    : null;
  const searchItems = root.instruments.flatMap((inst) => {
    if (!inst.available) {
      return [
        {
          href: `/instruments/${inst.slug}/`,
          title: inst.title,
          subtitle: "Not available in this data mode",
          haystack: `${inst.title} ${inst.instrument_id}`,
        },
      ];
    }
    const sections = loadSections(inst.slug).sections as Array<{
      section_id: string;
      latest_num?: string;
      latest_heading?: string;
      nums_seen: string[];
      headings_seen: string[];
    }>;
    return [
      {
        href: `/instruments/${inst.slug}/`,
        title: inst.title,
        subtitle: `${inst.version_count} snapshots · ${inst.section_count} sections`,
        haystack: `${inst.title} ${inst.instrument_id} ${inst.slug}`,
      },
      ...sections.map((s) => ({
        href: `/instruments/${inst.slug}/sections/${encodeURIComponent(s.section_id)}/`,
        title: `${inst.instrument_id} § ${s.latest_num || s.nums_seen[0] || "—"}`,
        subtitle: s.latest_heading || s.headings_seen[0] || s.section_id,
        haystack: [
          inst.instrument_id,
          s.section_id,
          ...(s.nums_seen || []),
          ...(s.headings_seen || []),
          s.latest_heading || "",
        ].join(" "),
      })),
    ];
  });

  const exampleHref =
    example && exampleSlug
      ? `/instruments/${exampleSlug}/sections/${encodeURIComponent(example.section_id)}/compare/${encodeURIComponent(example.from_version)}/${encodeURIComponent(example.to_version)}/`
      : null;

  return (
    <>
      <section className="hero hero-rc1">
        <p className="brand-mark">LawTrace HK</p>
        <h1>{HERO_HEADING}</h1>
        <p className="lede">{HERO_SUBHEADING}</p>
        <p className="meta product-promise">{PRODUCT_PROMISE}</p>
        <div className="cta-row">
          {exampleHref ? (
            <Link className="btn" href={exampleHref}>
              Explore a real change
            </Link>
          ) : (
            <Link className="btn" href="/collections/">
              Browse collections
            </Link>
          )}
          <Link className="btn secondary" href="/methodology/">
            Methodology
          </Link>
        </div>
        <ul className="trust-strip" aria-label="Trust indicators">
          <li>
            <strong>Deterministic</strong>
            <span>Same inputs yield the same comparison.</span>
          </li>
          <li>
            <strong>Source-linked</strong>
            <span>Every row carries file hashes and provenance.</span>
          </li>
          <li>
            <strong>Reconstruction tested</strong>
            <span>Supported diffs must rebuild snapshot B from A.</span>
          </li>
        </ul>
        <StatusNotice variant="inline" />
      </section>

      <section>
        <h2 className="section-title">Collections</h2>
        <div className="grid-2" style={{ marginTop: "1rem" }}>
          {root.instruments.map((inst) => {
            const badge = instrumentCompletenessBadge(inst);
            return (
              <article
                key={inst.slug}
                className={`card ${inst.available ? "" : "unavailable"}`}
              >
                <div className="card-head">
                  <h3>{inst.title}</h3>
                  {badge ? (
                    <span className={`mode-badge tone-${badge.tone}`}>
                      {badge.label}
                    </span>
                  ) : null}
                </div>
                {inst.available ? (
                  <>
                    <p className="meta">
                      {inst.version_count} official open-data snapshots ·{" "}
                      {inst.section_count} tracked top-level sections
                      {inst.sampling && !inst.sampling.complete
                        ? ` · sampled ${inst.sampling.versions_included}/${inst.sampling.total_available_versions} (not complete)`
                        : ""}
                    </p>
                    <p>
                      <Link className="btn" href={`/instruments/${inst.slug}/`}>
                        Open instrument
                      </Link>
                    </p>
                  </>
                ) : (
                  <>
                    <p className="meta">{inst.missing_reason}</p>
                    <p>
                      <Link
                        className="btn secondary"
                        href={`/instruments/${inst.slug}/`}
                      >
                        View status
                      </Link>
                    </p>
                  </>
                )}
              </article>
            );
          })}
        </div>
      </section>

      {example && exampleHref ? (
        <section style={{ marginTop: "2rem" }}>
          <h2 className="section-title">Featured comparison</h2>
          <div className="card featured" style={{ marginTop: "0.75rem" }}>
            <p className="meta">
              {example.instrument_id} · {relationshipLabel(example.relationship)}
            </p>
            <p className="lede" style={{ fontSize: "1.15rem" }}>
              A real consecutive-snapshot change in Cap.{" "}
              {example.instrument_id.replace("cap:", "")} § {example.heading || "—"}.
            </p>
            <Link className="btn" href={exampleHref}>
              Open evidence
            </Link>
          </div>
        </section>
      ) : null}

      <section style={{ marginTop: "2rem" }}>
        <h2 className="section-title">Search</h2>
        <SearchList
          items={searchItems}
          placeholder="Search by chapter, section number, heading, or @id"
        />
      </section>

      <details className="disclaimer-details">
        <summary>Full status notice</summary>
        <StatusNotice />
      </details>
    </>
  );
}
