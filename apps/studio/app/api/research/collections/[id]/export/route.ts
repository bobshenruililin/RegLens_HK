import { NextResponse } from "next/server";
import { requireUser } from "../../../../../../lib/auth-server";
import { buildResearchCollectionExport } from "../../../../../../lib/research-data";

export const dynamic = "force-dynamic";

export async function GET(
  _req: Request,
  {
    params,
  }: {
    params: { id: string };
  }
) {
  const user = await requireUser();
  const bundle = await buildResearchCollectionExport(params.id);
  if (!bundle) {
    return NextResponse.json({ error: "collection not found" }, { status: 404 });
  }
  console.info("research_collection.export", {
    actor: user.username,
    collection_id: bundle.collection.id,
    decision_count: bundle.collection.decision_ids.length,
  });
  return NextResponse.json({
    warning:
      "INTERNAL USE ONLY - Synthetic demo research export. Primary sources remain authoritative. Not legal advice.",
    ...bundle,
  });
}
