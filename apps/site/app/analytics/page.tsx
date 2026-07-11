import { BarChart } from "@/components/charts/BarChart";
import { Heatmap } from "@/components/charts/Heatmap";
import { LinkedCountTable } from "@/components/DataTable";
import { SyntheticBanner } from "@/components/SyntheticBanner";
import { exploreHref, loadAnalytics, loadRelease } from "@/lib/release";

export const metadata = {
  title: "Analytics",
};

export default function AnalyticsPage() {
  const release = loadRelease();
  const analytics = loadAnalytics();

  const yearItems = (analytics.year_rows || []).map((row) => ({
    label: String(row.year),
    count: row.count,
    href: exploreHref({ year: String(row.year) }),
  }));

  const regulatorItems = (analytics.regulator_rows || []).map((row) => ({
    label: row.regulator,
    count: row.count,
    href: exploreHref({ regulator: row.regulator }),
  }));

  const sanctionItems = (analytics.sanction_rows || []).map((row) => ({
    label: row.sanction,
    count: row.count,
    href: exploreHref({ sanction: row.sanction }),
  }));

  const heatmapCells = analytics.heatmap_rows || [];

  return (
    <>
      <SyntheticBanner kind={release.kind} version={release.version} />

      <header className="page-hero">
        <h1>Analytics</h1>
        <p className="lede">
          Aggregate views for the current release. Every chart bar and heatmap
          cell links to a filtered explore query. Charts are SVG/CSS only; data
          tables are provided as accessible alternatives.
        </p>
      </header>

      <aside className="banner" role="note" aria-label="Corpus disclaimer">
        <strong>Corpus disclaimer</strong>
        <p>
          {analytics.bias_warning ||
            "These figures describe decisions in the published corpus and do not represent complaint or misconduct rates."}{" "}
          Release <code>{release.version}</code> ({release.kind}).
        </p>
      </aside>

      <section className="section" aria-labelledby="year-heading">
        <h2 id="year-heading">Published decisions by year</h2>
        <BarChart title="Decisions by year" items={yearItems} />
        <LinkedCountTable
          caption="Decisions by year (data table)"
          rows={yearItems.map((i) => ({
            label: i.label,
            count: i.count,
            href: i.href!,
          }))}
        />
      </section>

      <section className="section" aria-labelledby="reg-heading">
        <h2 id="reg-heading">By regulator</h2>
        <BarChart title="Decisions by regulator" items={regulatorItems} />
        <LinkedCountTable
          caption="Decisions by regulator (data table)"
          rows={regulatorItems.map((i) => ({
            label: i.label,
            count: i.count,
            href: i.href!,
          }))}
        />
      </section>

      <section className="section" aria-labelledby="sanction-heading">
        <h2 id="sanction-heading">Sanction distribution</h2>
        <BarChart title="Sanctions" items={sanctionItems} />
        <LinkedCountTable
          caption="Sanction distribution (data table)"
          rows={sanctionItems.map((i) => ({
            label: i.label,
            count: i.count,
            href: i.href!,
          }))}
        />
      </section>

      <section className="section" aria-labelledby="heat-heading">
        <h2 id="heat-heading">Issue × sanction</h2>
        <Heatmap title="Issue × sanction heatmap" cells={heatmapCells} />
        <LinkedCountTable
          caption="Issue × sanction pairs (data table)"
          rows={heatmapCells.map((c) => ({
            label: `${c.issue} × ${c.sanction}`,
            count: c.count,
            href: exploreHref({ issue: c.issue, sanction: c.sanction }),
          }))}
        />
      </section>
    </>
  );
}
