import { listDecisions, loadDecision } from "../../../lib/data";
import { getMode, isDemoMode, isPostgresMode } from "../../../lib/mode";
import { getDecisionReviewBundle, listDecisionNavigationPg } from "../../../lib/pg-data";
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
    const ordered = listDecisions().sort((a, b) =>
      `${a.regulator_code}:${a.case_ref || a.title}`.localeCompare(
        `${b.regulator_code}:${b.case_ref || b.title}`
      )
    );
    const idx = ordered.findIndex((d) => d.id === decisionId);
    const previousId = idx > 0 ? ordered[idx - 1].id : null;
    const nextId = idx >= 0 && idx < ordered.length - 1 ? ordered[idx + 1].id : null;
    return (
      <ReviewDecisionClient
        decisionId={decisionId}
        mode="demo"
        previousDecisionId={previousId}
        nextDecisionId={nextId}
        demo={
          decision
            ? {
                title: decision.title,
                regulator: decision.regulator_code,
                external_ref: decision.case_ref || decision.id,
                source_id: decision.source_id,
                licence_notice: decision.licence_notice,
                defendant_name_as_published: decision.defendant_name_as_published,
                pages: decision.pages,
                propositions: decision.propositions.map((p) => ({
                  id: p.id,
                  client_ref: "client_ref" in p ? String(p.client_ref) : p.id,
                  prop_type: p.prop_type,
                  epistemic_class: p.epistemic_class,
                  claim_text: p.claim_text,
                  review_status: p.review_status,
                  critic_result:
                    "critic_result" in p
                      ? p.critic_result
                      : "critic" in p
                        ? p.critic
                        : "critic_output" in p
                          ? p.critic_output
                          : null,
                  evidence: p.evidence.map((e) => ({
                    page_no: e.page_no,
                    quote: e.quote,
                    text_variant:
                      "text_variant" in e && typeof e.text_variant === "string"
                        ? e.text_variant
                        : null,
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
  const ordered = await listDecisionNavigationPg();
  const idx = ordered.findIndex((d) => d.id === decisionId);
  const previousId = idx > 0 ? ordered[idx - 1].id : null;
  const nextId = idx >= 0 && idx < ordered.length - 1 ? ordered[idx + 1].id : null;
  return (
    <ReviewDecisionClient
      decisionId={decisionId}
      mode="postgres"
      previousDecisionId={previousId}
      nextDecisionId={nextId}
      postgres={bundle}
    />
  );
}
