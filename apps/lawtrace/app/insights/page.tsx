import Link from "next/link";
import { StatusNotice } from "@/components/StatusNotice";
import {
  loadInsights,
  loadRootManifest,
  loadTransitionsIndex,
} from "@/lib/data";
import { FREQUENCY_NOTE } from "@/lib/disclaimer";
import { instrumentCompletenessBadge } from "@/lib/mode";

export default function InsightsPage() {
  const root = loadRootManifest();
  const available = root.instruments.filter((i) => i.available);

  return (
    <>
      <h1 className="page-title">Insights</h1>
      <StatusNotice variant="inline" />
      <p className="meta">
        Deterministic descriptive metrics only. {FREQUENCY_NOTE} Figures do not
        measure legislative intent or public-health effect.
      </p>
      {!available.length ? (
        <p className="muted">No instruments available in this dataset mode.</p>
      ) : null}
      {available.map((inst) => {
        const badge = instrumentCompletenessBadge(inst);
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
            from_version?: string;
            to_version?: string;
            changed_count: number;
          }>;
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
          renderability_distribution: Record<string, number>;
          reconstruction: { ok: number; total: number; rate: number };
          sampling: {
            complete: boolean;
            versions_included: number;
            total_available_versions: number;
          };
        };
        const maxChanged = Math.max(
          1,
          ...insights.transitions.map((t) => t.changed_count),
        );
        const transitionsIndex = loadTransitionsIndex(inst.slug)
          .transitions as Array<{
          transition_id: string;
          from_version: string;
          to_version: string;
        }>;
        const byId = Object.fromEntries(
          transitionsIndex.map((t) => [t.transition_id, t]),
        );

        return (
          <section key={inst.slug} style={{ marginTop: "2rem" }}>
            <div className="card-head">
              <h2 className="section-title">{inst.title}</h2>
              {badge ? (
                <span className={`mode-badge tone-${badge.tone}`}>
                  {badge.label}
                </span>
              ) : null}
            </div>
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
            <ul className="plain-list">
              {Object.entries(insights.relationship_totals).map(([k, v]) => (
                <li key={k}>
                  {k}: {v}
                </li>
              ))}
            </ul>

            {insights.textual_vs_status ? (
              <>
                <h3>Textual versus status</h3>
                <ul className="plain-list">
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
                <ul className="plain-list">
                  <li>
                    Additions: {insights.token_flow.legal_text_token_additions}
                  </li>
                  <li>
                    Deletions: {insights.token_flow.legal_text_token_deletions}
                  </li>
                </ul>
              </>
            ) : null}

            <h3>Activity by transition</h3>
            {insights.transitions.map((t) => {
              const meta = byId[t.transition_id];
              const href = meta
                ? `/instruments/${inst.slug}/transitions/${encodeURIComponent(meta.from_version)}/${encodeURIComponent(meta.to_version)}/`
                : `/instruments/${inst.slug}/`;
              return (
                <div className="bar-row" key={t.transition_id}>
                  <div className="meta">
                    <Link href={href}>
                      {t.to_label.replace(
                        "Official open-data snapshot dated ",
                        "",
                      )}
                    </Link>
                  </div>
                  <div className="bar" aria-hidden="true">
                    <span
                      style={{
                        width: `${(100 * t.changed_count) / maxChanged}%`,
                      }}
                    />
                  </div>
                  <div>{t.changed_count}</div>
                </div>
              );
            })}

            <h3>Sections with most descriptive changes</h3>
            <p className="meta">{FREQUENCY_NOTE}</p>
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th scope="col">Section</th>
                    <th scope="col">Count</th>
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
            <ul className="plain-list">
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
