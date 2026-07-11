import { loadDecision } from "../../../lib/data";
import { getMode, isDemoMode, isPostgresMode } from "../../../lib/mode";
import { getDecisionReviewBundle } from "../../../lib/pg-data";
import { ReviewDecisionClient } from "../../../components/ReviewDecisionClient";

export const dynamic = "force-dynamic";

export default async function ReviewDecisionPage({
  params,
}: {
  params: { "decision-id": string };
}) {
  const decisionId = params["decision-id"];
  const mode = getMode();

  if (isDemoMode()) {
    const decision = loadDecision(decisionId);
    return (
      <ReviewDecisionClient
        decisionId={decisionId}
        mode="demo"
        demo={
          decision
            ? {
                title: decision.title,
                regulator: decision.regulator_code,
                pages: decision.pages,
                propositions: decision.propositions.map((p) => ({
                  id: p.id,
                  prop_type: p.prop_type,
                  epistemic_class: p.epistemic_class,
                  claim_text: p.claim_text,
                  review_status: p.review_status,
                  evidence: p.evidence.map((e) => ({
                    page_no: e.page_no,
                    quote: e.quote,
                  })),
                })),
              }
            : null
        }
      />
    );
  }

  if (!isPostgresMode()) {
    return (
      <section className="panel">
        <h1>Review</h1>
        <p className="warning">Unsupported mode.</p>
      </section>
    );
  }

  const bundle = await getDecisionReviewBundle(decisionId);
  return (
    <ReviewDecisionClient
      decisionId={decisionId}
      mode="postgres"
      postgres={bundle}
    />
  );
}
