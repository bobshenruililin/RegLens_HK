import Link from "next/link";
import { notFound } from "next/navigation";
import { SyntheticBanner } from "@/components/SyntheticBanner";
import {
  loadCatalog,
  loadPublicDecision,
  loadRelease,
  type PublicDecision,
} from "@/lib/release";

type PageProps = {
  params: { slug: string };
};

export const dynamicParams = false;

export function generateStaticParams() {
  const catalog = loadCatalog();
  return catalog.decisions.map((d) => ({ slug: d.slug }));
}

export function generateMetadata({ params }: PageProps) {
  const decision = loadPublicDecision(params.slug);
  if (!decision) return { title: "Decision not found" };
  return { title: decision.title };
}

function PropBlock({ decision }: { decision: PublicDecision }) {
  if (!decision.propositions?.length) {
    return (
      <p className="empty-state">
        No structured propositions are included for this decision in the release.
      </p>
    );
  }
  return (
    <ul className="decision-list">
      {decision.propositions.map((p) => (
        <li key={p.client_ref} className="decision-card">
          <div className="meta-row">
            <span className="tag-source">{p.prop_type}</span>
            <span>{p.epistemic_class}</span>
            <span>{p.verification_status}</span>
          </div>
          <p>{p.claim_text}</p>
          <div className="evidence">
            {p.evidence.map((ev, idx) => (
              <p key={`${p.client_ref}-${idx}`} className="excerpt">
                <span className="label">Source excerpt · page {ev.page_no}</span>
                <br />
                “{ev.excerpt}”
              </p>
            ))}
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function DecisionPage({ params }: PageProps) {
  const release = loadRelease();
  const decision = loadPublicDecision(params.slug);
  if (!decision) notFound();

  const judgment =
    decision.dates?.judgment || decision.dates?.inquiry || null;

  return (
    <>
      <SyntheticBanner kind={release.kind} version={release.version} />

      <header className="page-hero">
        <p className="meta-row">
          <Link href="/explore/">Explore</Link>
          <span aria-hidden="true">/</span>
          <span>{decision.regulator_code}</span>
        </p>
        <h1>{decision.title}</h1>
        {decision.editorial_takeaway?.takeaway ? (
          <p className="lede editorial">
            <strong>Editorial takeaway.</strong>{" "}
            {decision.editorial_takeaway.takeaway}
          </p>
        ) : null}
      </header>

      {decision.editorial_takeaway?.summary ? (
        <section className="section" aria-labelledby="summary-heading">
          <h2 id="summary-heading">Verified editorial summary</h2>
          <p className="editorial">{decision.editorial_takeaway.summary}</p>
          <p className="meta-row">
            Status: {decision.editorial_takeaway.status}
          </p>
        </section>
      ) : null}

      <dl className="detail-dl">
        <dt>Case refs</dt>
        <dd>{(decision.case_refs || []).join(", ") || "—"}</dd>
        <dt>Inquiry / judgment dates</dt>
        <dd>
          inquiry {decision.dates?.inquiry || "—"} · judgment{" "}
          {decision.dates?.judgment || "—"}
        </dd>
        <dt>Primary date</dt>
        <dd>{judgment || "—"}</dd>
        <dt>Regulator</dt>
        <dd>{decision.regulator_code}</dd>
        <dt>Profession</dt>
        <dd>{decision.profession || "—"}</dd>
        <dt>Official source</dt>
        <dd>
          {decision.official_source_url ? (
            <a href={decision.official_source_url} rel="noopener noreferrer">
              Open official source
            </a>
          ) : (
            "—"
          )}
        </dd>
        <dt>Source attribution</dt>
        <dd>{decision.source_attribution || "—"}</dd>
        <dt>Release / verification</dt>
        <dd>
          {release.version} · {decision.release_mode || release.kind}
        </dd>
      </dl>

      {(decision.publication_policy_caveats || []).length > 0 ? (
        <aside className="banner" role="note">
          <strong>Publication policy</strong>
          <ul>
            {decision.publication_policy_caveats!.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </aside>
      ) : null}

      <section className="section" aria-labelledby="class-heading">
        <h2 id="class-heading">Editorial classifications</h2>
        <p className="meta-row">
          Normalized codes are editorial labels, distinct from source wording.
        </p>
        <dl className="detail-dl">
          <dt>Issues</dt>
          <dd>{(decision.issue_categories || []).join(", ") || "—"}</dd>
          <dt>Findings</dt>
          <dd>{(decision.finding_outcomes || []).join(", ") || "—"}</dd>
          <dt>Sanctions</dt>
          <dd>{(decision.sanction_categories || []).join(", ") || "—"}</dd>
          <dt>Factors</dt>
          <dd>{(decision.factor_categories || []).join(", ") || "—"}</dd>
        </dl>
      </section>

      <section className="section" aria-labelledby="props-heading">
        <h2 id="props-heading">Published propositions</h2>
        <p>
          Source-derived claims with public evidence excerpts (not full page
          text).
        </p>
        <PropBlock decision={decision} />
      </section>

      {(decision.relations || []).length > 0 ? (
        <section className="section" aria-labelledby="rel-heading">
          <h2 id="rel-heading">Charge → finding → sanction relationships</h2>
          <ul>
            {decision.relations!.map((r, i) => (
              <li key={i}>
                {r.relation_type}: {r.from_ref} → {r.to_ref}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {(decision.coverage_warnings || []).length > 0 ? (
        <section className="section">
          <h2>Coverage warnings</h2>
          <ul>
            {decision.coverage_warnings!.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <p>
        <Link className="btn btn--ghost" href={`/compare/?ids=${decision.slug}`}>
          Add to compare
        </Link>
      </p>
    </>
  );
}
