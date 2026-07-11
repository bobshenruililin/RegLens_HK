"use client";

import { useEffect } from "react";
import type { DecisionSeed } from "../lib/decision";

export function DecisionView({ decision }: { decision: DecisionSeed }) {
  useEffect(() => {
    const hash = window.location.hash.replace("#", "");
    if (!hash) return;
    const el = document.getElementById(hash);
    if (el) {
      el.classList.add("highlight");
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, []);

  const published = decision.propositions.filter((p) => p.published);
  const missing = decision.coverage?.missing_fields ?? [];
  const warnings = decision.coverage?.warnings ?? [];

  return (
    <article>
      <section className="panel">
        <div className="badge">{decision.regulator_code}</div>
        <div className="badge">{decision.profession}</div>
        <h1 className="brand" style={{ fontSize: "2rem", marginTop: "0.6rem" }}>
          {decision.title}
        </h1>
        <p>{decision.licence_notice}</p>
        <dl className="meta-grid">
          <div>
            <dt>Case reference</dt>
            <dd>{decision.case_ref || "—"}</dd>
          </div>
          <div>
            <dt>Decision date</dt>
            <dd>{decision.decision_date || "—"}</dd>
          </div>
          <div>
            <dt>Practitioner (as published)</dt>
            <dd>{decision.defendant_name_as_published || "—"}</dd>
          </div>
          <div>
            <dt>Registration no.</dt>
            <dd>{decision.defendant_registration_no || "—"}</dd>
          </div>
          <div>
            <dt>Official source</dt>
            <dd>
              {decision.source_url ? (
                <a href={decision.source_url} rel="noreferrer" target="_blank">
                  Open primary source
                </a>
              ) : (
                "Synthetic fixture (no external URL)"
              )}
            </dd>
          </div>
        </dl>
        {(missing.length > 0 || warnings.length > 0) && (
          <div className="warning">
            <strong>Coverage warnings</strong>
            <ul>
              {missing.map((m) => (
                <li key={m}>Missing field: {m}</li>
              ))}
              {warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="panel" style={{ marginTop: "1rem" }}>
        <h2>Extracted propositions</h2>
        <div className="prop-list">
          {published.map((prop) => (
            <div className="prop" key={prop.id} id={`prop-${prop.id}`}>
              <div className="prop-type">
                {prop.prop_type} · {prop.epistemic_class} · conf{" "}
                {prop.confidence.toFixed(2)}
              </div>
              <p className="claim">{prop.claim_text}</p>
              <div className="evidence">
                {prop.evidence.map((ev, idx) => (
                  <div key={`${prop.id}-${idx}`}>
                    <a href={`#page-${ev.page_no}`}>
                      Source: page {ev.page_no}
                      {ev.span_id ? ` · span ${ev.span_id.slice(0, 8)}` : ""}
                    </a>
                    <div style={{ color: "var(--muted)", marginTop: "0.25rem" }}>
                      “{ev.quote}”
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel" style={{ marginTop: "1rem" }}>
        <h2>Source pages</h2>
        {decision.pages.map((page) => (
          <div
            className="page-block"
            id={`page-${page.page_no}`}
            key={page.span_id}
          >
            <strong>
              Page {page.page_no}{" "}
              <span className="badge">{page.span_id.slice(0, 8)}</span>
            </strong>
            <pre>{page.text}</pre>
          </div>
        ))}
      </section>
    </article>
  );
}
