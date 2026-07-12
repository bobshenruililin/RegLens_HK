import Link from "next/link";
import { StatusNotice } from "@/components/StatusNotice";
import { loadInsights, loadRootManifest } from "@/lib/data";

export default function InsightsPage() {
  const root = loadRootManifest();
  const available = root.instruments.filter((i) => i.available);

  return (
    <>
      <h1 className="page-title">Insights</h1>
      <StatusNotice compact />
      <p className="meta">
        Deterministic descriptive metrics only. These figures do not measure
        legal importance, legislative intent, or public-health effect.
      </p>
      {available.map((inst) => {
        const insights = loadInsights(inst.slug) as {
          relationship_totals: Record<string, number>;
          sections_changed_most_frequently: Array<{
            section_id: string;
            descriptive_change_count: number;
            latest_num?: string;
            latest_heading?: string;
          }>;
          transitions: Array<{
            transition_id: string;
            from_label: string;
            to_label: string;
            changed_count: number;
          }>;
          renderability_distribution: Record<string, number>;
          textual_vs_status?: {
            text_changed_events: number;
            status_only_events: number;
            added: number;
            removed: number;
          };
          token_flow?: {
            legal_text_token_additions: number;
            legal_text_token_deletions: number;
          };
          reconstruction: { ok: number; total: number; rate: number };
          sampling: { complete: boolean; versions_included: number; total_available_versions: number };
        };
        const maxChanged = Math.max(
          1,
          ...insights.transitions.map((t) => t.changed_count),
        );
        return (
          <section key={inst.slug} style={{ marginTop: "2rem" }}>
            <h2 className="section-title">{inst.title}</h2>
            <p className="meta">
              Sampling:{" "}
              {insights.sampling.complete
                ? "complete export for available snapshots"
                : `sampled ${insights.sampling.versions_included}/${insights.sampling.total_available_versions} (not complete)`}
              {" · "}
              Reconstruction {insights.reconstruction.ok}/
              {insights.reconstruction.total}
            </p>
            <h3>Relationship totals</h3>
            <ul>
              {Object.entries(insights.relationship_totals).map(([k, v]) => (
                <li key={k}>
                  {k}: {v}
                </li>
              ))}
            </ul>
            {insights.textual_vs_status ? (
              <>
                <h3>Textual versus status channels</h3>
                <ul>
                  <li>
                    Textual change events:{" "}
                    {insights.textual_vs_status.text_changed_events}
                  </li>
                  <li>
                    Status-only events:{" "}
                    {insights.textual_vs_status.status_only_events}
                  </li>
                  <li>Additions: {insights.textual_vs_status.added}</li>
                  <li>Removals: {insights.textual_vs_status.removed}</li>
                </ul>
              </>
            ) : null}
            {insights.token_flow ? (
              <>
                <h3>Legal-text token flow</h3>
                <ul>
                  <li>
                    Token additions:{" "}
                    {insights.token_flow.legal_text_token_additions}
                  </li>
                  <li>
                    Token deletions:{" "}
                    {insights.token_flow.legal_text_token_deletions}
                  </li>
                </ul>
              </>
            ) : null}
            <h3>Change activity by transition</h3>
            {insights.transitions.map((t) => (
              <div className="bar-row" key={t.transition_id}>
                <div className="meta">{t.to_label.replace("Official open-data snapshot dated ", "")}</div>
                <div className="bar" aria-hidden="true">
                  <span
                    style={{ width: `${(100 * t.changed_count) / maxChanged}%` }}
                  />
                </div>
                <div>{t.changed_count}</div>
              </div>
            ))}
            <h3>Sections with most descriptive changes</h3>
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>Section</th>
                    <th>Descriptive count</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {insights.sections_changed_most_frequently.map((s) => (
                    <tr key={s.section_id}>
                      <td>
                        § {s.latest_num || "—"} · {s.latest_heading}
                      </td>
                      <td>{s.descriptive_change_count}</td>
                      <td>
                        <Link
                          href={`/instruments/${inst.slug}/sections/${encodeURIComponent(s.section_id)}/`}
                        >
                          History
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <h3>Renderability distribution</h3>
            <ul>
              {Object.entries(insights.renderability_distribution).map(
                ([k, v]) => (
                  <li key={k}>
                    {k}: {v}
                  </li>
                ),
              )}
            </ul>
          </section>
        );
      })}
    </>
  );
}
