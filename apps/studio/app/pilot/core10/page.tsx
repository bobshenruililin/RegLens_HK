import Link from "next/link";
import { requireUser } from "../../../lib/auth-server";
import { getCore10Progress } from "../../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function PilotCore10Page() {
  await requireUser();
  const progress = await getCore10Progress();

  return (
    <section className="panel">
      <p className="warning">{progress.spec.statistical_note}</p>
      <h1>Core 10 pilot</h1>
      <p>{progress.spec.purpose}</p>
      <p>{progress.spec.operator_note}</p>
      <dl className="meta-grid">
        <div>
          <dt>Planned</dt>
          <dd>{progress.counts.planned}</dd>
        </div>
        <div>
          <dt>Included</dt>
          <dd>{progress.counts.included}</dd>
        </div>
        <div>
          <dt>Blocked</dt>
          <dd>{progress.counts.blocked}</dd>
        </div>
        <div>
          <dt>Acquired</dt>
          <dd>{progress.counts.acquired}</dd>
        </div>
        <div>
          <dt>Extracted</dt>
          <dd>{progress.counts.extracted}</dd>
        </div>
        <div>
          <dt>Critic ready</dt>
          <dd>{progress.counts.critic_ready}</dd>
        </div>
        <div>
          <dt>Reviewed</dt>
          <dd>{progress.counts.reviewed}</dd>
        </div>
        <div>
          <dt>Complete</dt>
          <dd>{progress.counts.complete}</dd>
        </div>
        <div>
          <dt>Second checked</dt>
          <dd>{progress.counts.second_checked}</dd>
        </div>
      </dl>
      {progress.counts.real_reviewed_decisions === 0 && (
        <p className="warning">
          Action required: no real reviewed Core 10 decisions exist. Replace the
          synthetic placeholder slots with real internal IDs, then complete
          source acquisition, extraction, critic checks, human review,
          completeness review, and second check.
        </p>
      )}
      <div className="prop-list">
        {progress.slots.map((slot) => (
          <div className="prop" key={slot.source_item_id}>
            <div className="prop-type">
              {slot.source_id} · {slot.inclusion_status} ·{" "}
              {slot.multi_charge ? "multi-charge" : "single-charge"}
            </div>
            <p className="claim">{slot.external_ref}</p>
            <p>{slot.rationale}</p>
            <dl className="meta-grid">
              <div>
                <dt>Acquisition</dt>
                <dd>{slot.acquisition_status}</dd>
              </div>
              <div>
                <dt>Extraction</dt>
                <dd>{slot.extraction_status}</dd>
              </div>
              <div>
                <dt>Critic</dt>
                <dd>{slot.critic_status}</dd>
              </div>
              <div>
                <dt>Review</dt>
                <dd>{slot.review_status}</dd>
              </div>
              <div>
                <dt>Completeness</dt>
                <dd>{slot.completeness_status}</dd>
              </div>
              <div>
                <dt>Second check</dt>
                <dd>{slot.second_check_status}</dd>
              </div>
            </dl>
            <Link href={`/pilot/core10/${slot.source_item_id}`}>Open slot</Link>
            {slot.reviewed_decision?.id && (
              <>
                {" · "}
                <Link href={`/review/${slot.reviewed_decision.id}`}>Review decision</Link>
              </>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
