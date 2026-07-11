import { listResearchDecisionOptions } from "../../lib/research-data";
import ResearchPackClient from "./ResearchPackClient";

export const dynamic = "force-dynamic";

export default async function ResearchPackPage() {
  const decisions = await listResearchDecisionOptions();

  return (
    <section className="panel">
      <h1>Research pack</h1>
      <p>
        Select reviewed decisions and export a Markdown narrative plus CSV
        proposition table. The export is generated from Studio data only and
        does not alter publication status.
      </p>
      <ResearchPackClient decisions={decisions} />
    </section>
  );
}
