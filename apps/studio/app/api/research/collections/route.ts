import { NextResponse } from "next/server";
import {
  AuthRequiredError,
  CsrfError,
  ForbiddenError,
  assertMutationSafe,
  recordAudit,
  requireUser,
} from "../../../../lib/auth-server";
import {
  createResearchCollection,
  listResearchCollections,
} from "../../../../lib/research-data";

export const dynamic = "force-dynamic";

function authError(err: unknown): NextResponse | null {
  if (
    err instanceof AuthRequiredError ||
    err instanceof ForbiddenError ||
    err instanceof CsrfError
  ) {
    return NextResponse.json({ error: err.message }, { status: err.status });
  }
  return null;
}

export async function GET() {
  try {
    await requireUser();
    return NextResponse.json({ collections: await listResearchCollections() });
  } catch (err) {
    const response = authError(err);
    if (response) return response;
    return NextResponse.json({ error: "list collections failed" }, { status: 400 });
  }
}

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as {
      title?: unknown;
      description?: unknown;
      decision_ids?: unknown;
      notes?: unknown;
      csrf?: string;
    };
    await assertMutationSafe(req, body.csrf);
    const user = await requireUser();
    const collection = await createResearchCollection(body);
    console.info("research_collection.create", {
      actor: user.username,
      collection_id: collection.id,
      decision_count: collection.decision_ids.length,
    });
    await recordAudit({
      actor: user.username,
      actorUserId: user.id,
      action: "research_collection.create",
      entityType: "research_collection",
      entityId: collection.id,
      afterJson: collection,
    }).catch(() => undefined);
    return NextResponse.json({ ok: true, collection }, { status: 201 });
  } catch (err) {
    const response = authError(err);
    if (response) return response;
    const message = err instanceof Error ? err.message : "create collection failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
