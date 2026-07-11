import { SyntheticBanner } from "@/components/SyntheticBanner";
import { loadRelease } from "@/lib/release";

export const metadata = {
  title: "Methodology",
};

export default function MethodologyPage() {
  const release = loadRelease();

  return (
    <>
      <SyntheticBanner kind={release.kind} version={release.version} />

      <header className="page-hero">
        <h1>Methodology</h1>
        <p className="lede">
          How RegLens Observatory scopes coverage, classifies propositions, and
          limits what this static research surface can claim.
        </p>
      </header>

      <article className="prose">
        <h2>Coverage</h2>
        <p>
          MVP regulators are the Medical Council of Hong Kong (MCHK) and the
          Dental Council of Hong Kong (DCHK). The Nursing Council of Hong Kong
          (NCHK) is out of scope for this release track.
        </p>
        <p>
          The public Observatory consumes a versioned publication release only.
          Internal Studio workflows, private raw documents, and experimental
          database search are not exposed here.
        </p>

        <h2>Publication policies</h2>
        <ul>
          <li>
            Only reviewed, evidence-backed propositions may enter a publication
            release.
          </li>
          <li>
            Synthetic demo releases are explicitly labeled and must not be
            mistaken for a complete official archive.
          </li>
          <li>
            Patient identifiers and unnecessary personal data should be minimized;
            the site does not claim full de-identification.
          </li>
          <li>
            This surface is read-only static HTML/JSON. There is no authentication,
            no cookies, and no server-side mutation API.
          </li>
        </ul>

        <h2>Taxonomy</h2>
        <p>
          Structured fields follow the shared RegLens contracts: regulator codes,
          professions, proposition types (charge, finding, sanction, and related
          classes), and epistemic class (<code>fact</code> vs{" "}
          <code>interpretation</code>). Issue and sanction labels in analytics are
          normalized tags from the release build, not free-form legal advice.
        </p>

        <h2>Search limitations</h2>
        <p>
          Explore supports <strong>keyword and structured-field search</strong>{" "}
          only (substring matching over catalog fields). The Observatory does not
          provide PostgreSQL full-text search, ranking engines, or semantic /
          embedding retrieval.
        </p>

        <h2>Analytical limitations</h2>
        <ul>
          <li>
            Charts describe the release corpus, not the underlying population of
            all disciplinary outcomes.
          </li>
          <li>
            Missing documents, delayed publication, and tagging gaps introduce
            selection bias.
          </li>
          <li>
            Heatmaps and sanction bars are descriptive counts — not causal
            inferences or predictions.
          </li>
          <li>
            Current release: <code>{release.version}</code> ({release.kind}),
            generated {release.generated_at}.
          </li>
        </ul>
      </article>
    </>
  );
}
