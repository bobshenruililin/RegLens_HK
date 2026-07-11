import Link from "next/link";
import { requireUser } from "../../lib/auth-server";
import {
  getCore10Progress,
  getResearchHomeCounts,
  listReviewedResearchDecisions,
} from "../../lib/research-data";

export const dynamic = "force-dynamic";

const researchQuestions = [
  "Which charge patterns recur across reviewed synthetic MCHK and DCHK examples?",
  "How do finding outcomes map to sanction categories in the reviewed demo corpus?",
  "Where do rules, legal tests, and cited authorities appear in the extraction surface?",
  "Which pilot slots still need acquisition, extraction, critic, review, and second-check work?",
];

export default async function ResearchHomePage() {
  await requireUser();
  const [counts, decisions, core10] = await Promise.all([
    getResearchHomeCounts(),
    listReviewedResearchDecisions(),
    getCore10Progress(),
  ]);

  return (
    <section className="panel">
      <p className="warning">
        Research Observatory in Studio is authenticated and internal. GitHub
        Pages remains public/static and does not expose real research routes or
        source material.
      </p>
      <h1>Research Observatory</h1>
      <p>
        Server-rendered exploration surface over reviewed synthetic/demo data.
        By default it uses accepted or edited current revisions when proposition
        review status is available.
      </p>
      <dl className="meta-grid">
        <div>
          <dt>Reviewed decisions</dt>
          <dd>{counts.decisions}</dd>
        </div>
        <div>
          <dt>Reviewed propositions</dt>
          <dd>{counts.propositions}</dd>
        </div>
        <div>
          <dt>Regulators</dt>
          <dd>{counts.regulators}</dd>
        </div>
        <div>
          <dt>Issue categories present</dt>
          <dd>{counts.issues}</dd>
        </div>
        <div>
          <dt>Sanction categories present</dt>
          <dd>{counts.sanctions}</dd>
        </div>
        <div>
          <dt>Rules / authorities</dt>
          <dd>{counts.authorities}</dd>
        </div>
      </dl>

      <h2>Research questions</h2>
      <ul>
        {researchQuestions.map((question) => (
          <li key={question}>{question}</li>
        ))}
      </ul>

      <h2>Core 10 progress</h2>
      <dl className="meta-grid">
        <div>
          <dt>Planned slots</dt>
          <dd>{core10.spec.planned_total}</dd>
        </div>
        <div>
          <dt>Included</dt>
          <dd>{core10.counts.included}</dd>
        </div>
        <div>
          <dt>Reviewed</dt>
          <dd>{core10.counts.reviewed}</dd>
        </div>
        <div>
          <dt>Real reviewed decisions</dt>
          <dd>{core10.counts.real_reviewed_decisions}</dd>
        </div>
      </dl>
      {core10.counts.real_reviewed_decisions === 0 && (
        <p className="warning">
          No real reviewed Core 10 decisions exist yet. Replace synthetic
          placeholder IDs in <code>publications/pilot/core10.v1.json</code>,
          run acquisition/extraction/critic, and complete review plus second
          check before using Core 10 for internal research.
        </p>
      )}

      <h2>Routes</h2>
      <p className="review-nav">
        <Link href="/research/explore">Explore</Link>
        <Link href="/research/compare">Compare</Link>
        <Link href="/research/issues">Issues</Link>
        <Link href="/research/sanctions">Sanctions</Link>
        <Link href="/research/rules">Rules</Link>
        <Link href="/research/authorities">Authorities</Link>
        <Link href="/research/coverage">Coverage</Link>
        <Link href="/research/collections">Collections</Link>
        <Link href="/pilot/core10">Pilot Core10</Link>
      </p>

      <h2>Reviewed demo decisions</h2>
      {decisions.length === 0 ? (
        <p>No reviewed synthetic/demo decisions are available.</p>
      ) : (
        <div className="prop-list">
          {decisions.map((decision) => (
            <div className="prop" key={decision.external_ref}>
              <div className="prop-type">
                {decision.regulator_code} · {decision.year || "year unknown"} ·{" "}
                {decision.reviewer_status}
              </div>
              <p className="claim">{decision.title || decision.external_ref}</p>
              <p>{decision.takeaway}</p>
              <Link href={`/research/compare?ids=${decision.id || decision.external_ref}`}>
                Compare view
              </Link>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
