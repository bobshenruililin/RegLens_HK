import Link from "next/link";
import { SyntheticBanner } from "@/components/SyntheticBanner";
import { exploreHref, loadPublicDecision, loadRelease } from "@/lib/release";

export const metadata = {
  title: "Guided tour",
};

const PIPELINE_STEPS = [
  {
    label: "1. Acquire",
    body: "Synthetic fixture bytes are hashed and tracked. Real acquisition stays internal to Studio/private storage.",
  },
  {
    label: "2. Extract",
    body: "The worker creates structured propositions for charge, finding, sanction, factor, authority, and related fields.",
  },
  {
    label: "3. Review",
    body: "Human review verifies evidence spans before any proposition can appear in a publication release.",
  },
  {
    label: "4. Release",
    body: "The public bundle contains only checked JSON/CSV, caveats, and excerpt-bounded evidence.",
  },
  {
    label: "5. Explore",
    body: "Observatory pages provide keyword and structured-field search over the published synthetic demo corpus.",
  },
] as const;

export default function TourPage() {
  const release = loadRelease();
  const decision = loadPublicDecision("syn-mchk-2024-001");
  const propositions = decision?.propositions || [];

  return (
    <>
      <SyntheticBanner kind={release.kind} version={release.version} />

      <header className="page-hero">
        <h1>Guided tour of the RegLens pipeline</h1>
        <p className="lede">
          Follow the synthetic decision <code>syn-mchk-2024-001</code> from
          fixture to structured public release. This is a demo, not a real MCHK
          judgment.
        </p>
      </header>

      <section className="section" aria-labelledby="pipeline-heading">
        <h2 id="pipeline-heading">Pipeline steps</h2>
        <div className="compare-grid">
          {PIPELINE_STEPS.map((step) => (
            <article className="compare-col" key={step.label}>
              <h3>{step.label}</h3>
              <p>{step.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section" aria-labelledby="decision-heading">
        <h2 id="decision-heading">Synthetic decision used in this tour</h2>
        {decision ? (
          <>
            <dl className="detail-dl">
              <dt>Title</dt>
              <dd>{decision.title}</dd>
              <dt>Regulator</dt>
              <dd>{decision.regulator_code}</dd>
              <dt>Profession</dt>
              <dd>{decision.profession}</dd>
              <dt>Fixture kind</dt>
              <dd>{decision.fixture_kind}</dd>
              <dt>Release mode</dt>
              <dd>{decision.release_mode}</dd>
            </dl>
            <p>
              The public page exposes reviewed, excerpt-bounded propositions. It
              does not expose raw source HTML/PDF, full page text, model
              confidence, or Studio review notes.
            </p>
            <div className="link-row">
              <Link className="btn" href="/decisions/syn-mchk-2024-001/">
                Open synthetic decision
              </Link>
              <Link
                className="btn btn--ghost"
                href={exploreHref({ q: "recordkeeping", regulator: "MCHK" })}
              >
                Search related demo records
              </Link>
            </div>
          </>
        ) : (
          <p className="empty-state">
            The synthetic decision is missing from the current release bundle.
          </p>
        )}
      </section>

      <section className="section" aria-labelledby="codebook-heading">
        <h2 id="codebook-heading">What gets coded</h2>
        <p>
          The tour decision demonstrates the RC4 editorial codebook categories
          using synthetic propositions only.
        </p>
        <ul className="decision-list">
          {propositions.slice(0, 8).map((prop) => (
            <li className="decision-card" key={prop.client_ref}>
              <h3>
                {prop.prop_type}{" "}
                <span className="meta-row">({prop.epistemic_class})</span>
              </h3>
              <p>{prop.claim_text}</p>
              <p className="meta-row">
                Derivation: {prop.derivation || "not stated"} / Status:{" "}
                {prop.verification_status}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section className="section" aria-labelledby="boundary-heading">
        <h2 id="boundary-heading">Public boundary</h2>
        <p>
          GitHub Pages is publicly accessible. Real Core10/Core50 corpus data
          stays in Studio/private storage until legal approval and source policy
          permit a public real release.
        </p>
      </section>
    </>
  );
}
