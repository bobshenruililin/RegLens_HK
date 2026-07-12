import { StatusNotice } from "@/components/StatusNotice";
import { loadMethodology } from "@/lib/data";
import { PRODUCT_PROMISE } from "@/lib/disclaimer";

export default function MethodologyPage() {
  const m = loadMethodology() as {
    date_semantics: string;
    identity: string;
    supported_relationships: string[];
    unsupported_or_candidate: string[];
    review_status_policy: string;
    attribution: { source: string; terms: string };
    corrections_contact_placeholder: string;
  };

  return (
    <>
      <h1 className="page-title">Methodology and limitations</h1>
      <StatusNotice />

      <h2 className="section-title">Product promise</h2>
      <p>{PRODUCT_PROMISE}</p>

      <h2 className="section-title">Processing pipeline</h2>
      <ol className="pipeline">
        <li>Official XML</li>
        <li>Secure parsing</li>
        <li>Stable section identity (@id)</li>
        <li>Deterministic comparison</li>
        <li>Reconstruction check</li>
        <li>LawTrace display</li>
      </ol>

      <h2 className="section-title">What a snapshot is</h2>
      <p>
        An official open-data XML version published through DATA.GOV.HK / HKeL.
        Labels read “Official open-data snapshot dated [date]”.
      </p>
      <h2 className="section-title">What a snapshot is not</h2>
      <p>
        A snapshot date is not a commencement date, effective date, or proof of
        the law in force on a selected calendar day.
      </p>

      <h2 className="section-title">Date semantics</h2>
      <p>
        <code>{m.date_semantics}</code>
      </p>

      <h2 className="section-title">Stable @id identity</h2>
      <p>{m.identity}</p>
      <p>
        Nested nodes without independent top-level @id are outside the MVP
        identity guarantee.
      </p>

      <h2 className="section-title">How redlines are generated</h2>
      <p>
        Legal text, structure, and status/metadata are compared as separate
        channels. Token operations are deterministic. Status-only changes are
        never presented as textual amendments.
      </p>

      <h2 className="section-title">Reconstruction testing</h2>
      <p>
        For supported pairs, applying recorded operations must rebuild snapshot
        B from snapshot A. Failures fail closed and are not silently accepted.
      </p>

      <h2 className="section-title">Renderability</h2>
      <p>
        Renderability describes whether ordinary redline display is fully
        supported for a section snapshot. Unsupported cases are labelled rather
        than invented.
      </p>

      <h2 className="section-title">Supported relationships</h2>
      <ul>
        {m.supported_relationships.map((x) => (
          <li key={x}>
            <code>{x}</code>
          </li>
        ))}
      </ul>
      <h2 className="section-title">Unsupported / candidate only</h2>
      <ul>
        {m.unsupported_or_candidate.map((x) => (
          <li key={x}>
            <code>{x}</code>
          </li>
        ))}
      </ul>

      <h2 className="section-title">Review status</h2>
      <p>{m.review_status_policy}</p>
      <p>
        The optional local review workspace is not authentication and does not
        mark algorithmic output as human-confirmed gold.
      </p>

      <h2 className="section-title">Attribution</h2>
      <p>
        {m.attribution.source}. Terms: {m.attribution.terms}. See{" "}
        <code>fixtures/lawtrace/ATTRIBUTION.md</code>.
      </p>

      <h2 className="section-title">Corrections</h2>
      <p>{m.corrections_contact_placeholder}</p>
    </>
  );
}
