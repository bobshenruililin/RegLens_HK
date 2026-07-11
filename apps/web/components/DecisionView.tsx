"use client";

import { useEffect } from "react";
import type { DecisionRecord } from "../lib/data";

function highlightQuote(text: string, quote: string): string {
  if (!quote) return escapeHtml(text);
  const idx = text.indexOf(quote);
  if (idx < 0) return escapeHtml(text);
  return (
    escapeHtml(text.slice(0, idx)) +
    '<mark class="evidence-mark">' +
    escapeHtml(quote) +
    "</mark>" +
    escapeHtml(text.slice(idx + quote.length))
  );
}

function escapeHtml(s: string): string {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function DecisionView({ decision }: { decision: DecisionRecord }) {
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
  const unpublished = decision.propositions.filter((p) => !p.published);
  const quotesByPage = new Map<number, string[]>();
  for (const prop of published) {
    for (const ev of prop.evidence) {
      const list = quotesByPage.get(ev.page_no) || [];
      list.push(ev.quote);
      quotesByPage.set(ev.page_no, list);
    }
  }

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
        <h2>Published propositions</h2>
        {published.length === 0 && (
          <p className="warning">
            Nothing published yet. Accept items in the review queue.
          </p>
        )}
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
        {unpublished.length > 0 && (
          <p style={{ marginTop: "1rem", color: "var(--muted)" }}>
            {unpublished.length} proposition(s) awaiting review (hidden from
            search).
          </p>
        )}
      </section>

      <section className="panel" style={{ marginTop: "1rem" }}>
        <h2>Source pages</h2>
        {decision.pages.map((page) => {
          const quotes = quotesByPage.get(page.page_no) || [];
          const html =
            quotes.length > 0
              ? highlightQuote(page.text, quotes[0])
              : escapeHtml(page.text);
          return (
            <div
              className="page-block"
              id={`page-${page.page_no}`}
              key={page.span_id}
            >
              <strong>
                Page {page.page_no}{" "}
                <span className="badge">{page.span_id.slice(0, 8)}</span>
              </strong>
              <pre dangerouslySetInnerHTML={{ __html: html }} />
            </div>
          );
        })}
      </section>
    </article>
  );
}
