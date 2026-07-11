import Link from "next/link";
import { isDemoMode, isPostgresMode } from "../../lib/mode";
import { listPendingReviews } from "../../lib/pg-data";
import ReviewQueueClient from "./ReviewQueueClient";

export const dynamic = "force-dynamic";

export default async function ReviewPage() {
  if (isDemoMode()) {
    return <ReviewQueueClient />;
  }

  if (!isPostgresMode()) {
    return (
      <section className="panel">
        <h1>Review queue</h1>
        <p className="warning">Unsupported REGLENS_MODE.</p>
      </section>
    );
  }

  const pending = await listPendingReviews();
  return (
    <section className="panel">
      <h1>Review queue</h1>
      <p>
        Postgres pending reviews. Open a decision for accept / edit / reject
        with optimistic concurrency.
      </p>
      {pending.length === 0 && <p>Queue empty.</p>}
      <div className="prop-list">
        {pending.map((item) => (
          <div className="prop" key={item.review_id}>
            <div className="prop-type">
              {item.regulator_code} · {item.prop_type} · {item.epistemic_class} ·
              rev {item.revision_number}
            </div>
            <p className="claim">{item.claim_text}</p>
            <p>
              <Link href={`/review/${item.decision_id}`}>
                {item.decision_title || item.external_ref}
              </Link>
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
