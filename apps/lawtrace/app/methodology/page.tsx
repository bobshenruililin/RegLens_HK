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
      <h2 className="section-title">Date semantics</h2>
      <p>
        <code>{m.date_semantics}</code> — snapshot labels identify official
        open-data XML versions. They are not commencement or effective dates.
      </p>
      <h2 className="section-title">Identity</h2>
      <p>{m.identity}</p>
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
      <h2 className="section-title">Attribution</h2>
      <p>
        {m.attribution.source}. {m.attribution.terms}.
      </p>
      <h2 className="section-title">Corrections</h2>
      <p className="meta">{m.corrections_contact_placeholder}</p>
    </>
  );
}
