import { loadDecision } from "../../../lib/decision";
import { DecisionView } from "../../../components/DecisionView";

export default function DecisionPage({
  params,
}: {
  params: { id: string };
}) {
  const decision = loadDecision(params.id);
  if (!decision) {
    return (
      <section className="panel">
        <h1>Decision not found</h1>
        <p>
          No seed for <code>{params.id}</code>. Run fixture ingest first.
        </p>
      </section>
    );
  }
  return <DecisionView decision={decision} />;
}
