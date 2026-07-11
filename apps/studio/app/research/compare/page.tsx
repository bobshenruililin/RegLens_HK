import Link from "next/link";
import { requireUser } from "../../../lib/auth-server";
import {
  getResearchDecisionSummaries,
  listResearchDecisionOptions,
} from "../../../lib/research-data";

export const dynamic = "force-dynamic";

function parseIds(searchParams: Record<string, string | string[] | undefined>): string[] {
  const raw = searchParams.ids;
  const values = Array.isArray(raw) ? raw : raw ? [raw] : [];
  return values.flatMap((value) => value.split(",")).filter(Boolean).slice(0, 4);
}

export default async function ResearchComparePage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  await requireUser();
  const selectedIds = parseIds(searchParams);
  const [options, selected] = await Promise.all([
    listResearchDecisionOptions(),
    getResearchDecisionSummaries(selectedIds),
  ]);

  return (
    <section className="panel">
      <h1>Compare decisions</h1>
      <p>Choose up to four reviewed decisions for side-by-side comparison.</p>
      <form method="get" style={{ display: "grid", gap: "0.75rem" }}>
        <fieldset style={{ border: "1px solid var(--line)", padding: "1rem" }}>
          <legend>Reviewed decisions</legend>
          <div className="prop-list">
            {options.map((option) => (
              <label key={option.id} className="prop">
                <input
                  type="checkbox"
                  name="ids"
                  value={option.id}
                  defaultChecked={selectedIds.includes(option.id)}
                />{" "}
                <span className="prop-type">
                  {option.regulator_code} · {option.external_ref}
                </span>
                <span className="claim" style={{ display: "block" }}>
                  {option.title}
                </span>
              </label>
            ))}
          </div>
        </fieldset>
        <div>
          <button type="submit">Compare selected</button>
        </div>
      </form>

      {selectedIds.length > 4 && (
        <p className="warning">Only the first four decisions are compared.</p>
      )}
      {selected.length === 0 ? (
        <p className="warning">
          No decisions selected. Start from <Link href="/research/explore">Explore</Link>{" "}
          or select reviewed demo decisions above.
        </p>
      ) : (
        <div
          style={{
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            marginTop: "1rem",
          }}
        >
          {selected.map((decision) => (
            <article className="prop" key={decision.external_ref}>
              <div className="prop-type">
                {decision.regulator_code} · {decision.year || "year unknown"}
              </div>
              <h2 className="claim">{decision.title || decision.external_ref}</h2>
              <p>{decision.summary}</p>
              <p style={{ color: "var(--muted)" }}>{decision.takeaway}</p>
              <dl className="meta-grid">
                <div>
                  <dt>Issues</dt>
                  <dd>{decision.issue_categories.join(", ") || "none"}</dd>
                </div>
                <div>
                  <dt>Findings</dt>
                  <dd>{decision.finding_outcomes.join(", ") || "none"}</dd>
                </div>
                <div>
                  <dt>Sanctions</dt>
                  <dd>{decision.sanction_categories.join(", ") || "none"}</dd>
                </div>
                <div>
                  <dt>Reviewed props</dt>
                  <dd>{decision.propositions.length}</dd>
                </div>
              </dl>
              <p>
                <strong>Charge:</strong>{" "}
                {decision.charge?.claim_text || "No reviewed charge"}
              </p>
              <p>
                <strong>Finding:</strong>{" "}
                {decision.finding?.claim_text || "No reviewed finding"}
              </p>
              <p>
                <strong>Sanction:</strong>{" "}
                {decision.sanction?.claim_text || "No reviewed sanction"}
              </p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
