import Link from "next/link";
import { StatusNotice } from "@/components/StatusNotice";
import { SearchList } from "@/components/SearchList";
import { loadRootManifest, loadSections } from "@/lib/data";
import { PRODUCT_PROMISE } from "@/lib/disclaimer";
import { relationshipLabel } from "@/lib/format";

export default function HomePage() {
  const root = loadRootManifest();
  const example = root.instruments.find((i) => i.available)?.example_comparison;
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

  return (
    <>
      <section className="hero">
        <p className="meta">Hong Kong open-data legislation comparator</p>
        <h1>LawTrace HK</h1>
        <p className="lede">{PRODUCT_PROMISE}</p>
        <StatusNotice />
      </section>

      <section>
        <h2 className="section-title">Collections</h2>
        <div className="grid-2" style={{ marginTop: "1rem" }}>
          {root.instruments.map((inst) => (
            <article
              key={inst.slug}
              className={`card ${inst.available ? "" : "unavailable"}`}
            >
              <h3>{inst.title}</h3>
              {inst.available ? (
                <>
                  <p className="meta">
                    {inst.version_count} official open-data snapshots ·{" "}
                    {inst.section_count} tracked top-level sections
                    {inst.sampling && !inst.sampling.complete
                      ? ` · sampled ${inst.sampling.versions_included}/${inst.sampling.total_available_versions}`
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
                    <Link className="btn secondary" href={`/instruments/${inst.slug}/`}>
                      View status
                    </Link>
                  </p>
                </>
              )}
            </article>
          ))}
        </div>
      </section>

      {example ? (
        <section style={{ marginTop: "2rem" }}>
          <h2 className="section-title">Example comparison</h2>
          <div className="card" style={{ marginTop: "0.75rem" }}>
            <p className="meta">
              {example.instrument_id} · {relationshipLabel(example.relationship)}
            </p>
            <p>
              Section <code>{example.section_id}</code> between consecutive
              snapshots.
            </p>
            <Link
              className="btn"
              href={`/instruments/${example.instrument_id.replace(":", "-").toLowerCase()}/sections/${encodeURIComponent(example.section_id)}/compare/${encodeURIComponent(example.from_version)}/${encodeURIComponent(example.to_version)}/`}
            >
              Open example
            </Link>
          </div>
        </section>
      ) : null}

      <section style={{ marginTop: "2rem" }}>
        <h2 className="section-title">Search instruments and sections</h2>
        <SearchList
          items={searchItems}
          placeholder="Search by chapter, section number, heading, or @id"
        />
      </section>
    </>
  );
}
