import Link from "next/link";
import { notFound } from "next/navigation";
import { requireUser } from "../../../../lib/auth-server";
import { getCore10Slot } from "../../../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function PilotCore10DecisionPage({
  params,
}: {
  params: { "decision-id": string };
}) {
  await requireUser();
  const slot = await getCore10Slot(params["decision-id"]);
  if (!slot) notFound();

  return (
    <section className="panel">
      <p>
        <Link href="/pilot/core10">Pilot Core10</Link>
      </p>
      <p className="warning">
        Core 10 slot is synthetic until an operator replaces the placeholder
        source identifiers and completes all review gates. It is not
        representative.
      </p>
      <h1>{slot.external_ref}</h1>
      <p>{slot.rationale}</p>
      <dl className="meta-grid">
        <div>
          <dt>Source item id</dt>
          <dd>{slot.source_item_id}</dd>
        </div>
        <div>
          <dt>Source id</dt>
          <dd>{slot.source_id}</dd>
        </div>
        <div>
          <dt>Case ref</dt>
          <dd>{slot.case_ref}</dd>
        </div>
        <div>
          <dt>Issue targets</dt>
          <dd>{slot.issue_targets.join(", ") || "none"}</dd>
        </div>
        <div>
          <dt>Multi-charge</dt>
          <dd>{slot.multi_charge ? "yes" : "no"}</dd>
        </div>
        <div>
          <dt>Inclusion</dt>
          <dd>{slot.inclusion_status}</dd>
        </div>
      </dl>
      <h2>Funnel gates</h2>
      <ol>
        <li>Acquisition: {slot.acquisition_status}</li>
        <li>Extraction: {slot.extraction_status}</li>
        <li>Critic: {slot.critic_status}</li>
        <li>Review: {slot.review_status}</li>
        <li>Completeness: {slot.completeness_status}</li>
        <li>Second check: {slot.second_check_status}</li>
      </ol>
      <h2>Decision match</h2>
      {slot.reviewed_decision ? (
        <div className="prop">
          <div className="prop-type">
            {slot.reviewed_decision.regulator_code} · {slot.reviewed_decision.reviewer_status}
          </div>
          <p className="claim">
            {slot.reviewed_decision.title || slot.reviewed_decision.external_ref}
          </p>
          <p>{slot.reviewed_decision.takeaway}</p>
          {slot.reviewed_decision.id && (
            <Link href={`/review/${slot.reviewed_decision.id}`}>Open review</Link>
          )}
        </div>
      ) : (
        <p className="warning">
          No reviewed decision matches this slot yet. Update{" "}
          <code>publications/pilot/core10.v1.json</code> with the real internal
          source item and external reference after acquisition, then run
          extraction and review.
        </p>
      )}
      <h2>Notes</h2>
      <p>{slot.notes}</p>
    </section>
  );
}
