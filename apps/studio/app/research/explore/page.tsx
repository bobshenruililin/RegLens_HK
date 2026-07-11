import { requireUser } from "../../../lib/auth-server";
import {
  getResearchFacets,
  listReviewedResearchDecisions,
  type ResearchExploreFilters,
} from "../../../lib/research-data";
import ExploreClient from "./ExploreClient";

export const dynamic = "force-dynamic";

export default async function ResearchExplorePage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  await requireUser();
  const value = (key: keyof ResearchExploreFilters) => {
    const raw = searchParams[key];
    return Array.isArray(raw) ? raw[0] : raw;
  };
  const initialFilters: ResearchExploreFilters = {
    regulator: value("regulator") || "",
    year: value("year") || "",
    issue: value("issue") || "",
    prop_type: value("prop_type") || "",
    q: value("q") || "",
  };
  const [decisions, facets] = await Promise.all([
    listReviewedResearchDecisions(),
    getResearchFacets(),
  ]);

  return (
    <section className="panel">
      <h1>Explore research decisions</h1>
      <p>
        URL-encoded filters over reviewed synthetic/demo decisions. Result cards
        surface charge, finding, sanction, and editorial takeaway fields.
      </p>
      <ExploreClient
        decisions={decisions}
        facets={facets}
        initialFilters={initialFilters}
      />
    </section>
  );
}
