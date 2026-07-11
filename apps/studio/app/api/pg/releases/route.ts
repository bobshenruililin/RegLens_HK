import { NextResponse } from "next/server";
import {
  AuthRequiredError,
  CsrfError,
  ForbiddenError,
  assertMutationSafe,
  requireRole,
} from "../../../../lib/auth-server";
import { isPostgresMode } from "../../../../lib/mode";
import { approveRelease, getRelease } from "../../../../lib/pg-data";

export async function GET(req: Request) {
  if (!isPostgresMode()) {
    return NextResponse.json(
      { error: "postgres mode required", releases: [] },
      { status: 400 }
    );
  }
  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");
  if (!id) {
    return NextResponse.json({ error: "id required" }, { status: 400 });
  }
  const release = await getRelease(id);
  if (!release) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }
  return NextResponse.json({ release });
}

/**
 * Approve a draft release (status → ready) with fail-closed SQL checks
 * mirroring Python approve_and_build_release.
 */
export async function POST(req: Request) {
  if (!isPostgresMode()) {
    return NextResponse.json(
      { error: "postgres mode required" },
      { status: 400 }
    );
  }
  try {
    const body = (await req.json()) as {
      publication_release_id?: string;
      expected_version?: number;
      csrf?: string;
    };
    await assertMutationSafe(req, body.csrf);
    const user = await requireRole("publisher");

    if (!body.publication_release_id || body.expected_version == null) {
      return NextResponse.json(
        { error: "publication_release_id and expected_version required" },
        { status: 400 }
      );
    }

    const result = await approveRelease({
      publicationReleaseId: body.publication_release_id,
      expectedVersion: body.expected_version,
      actorUserId: user.id,
    });

    if (result.errors?.length) {
      return NextResponse.json(
        {
          ok: false,
          error: "Release validation failed (fail-closed)",
          errors: result.errors,
        },
        { status: 400 }
      );
    }

    return NextResponse.json({ ok: true, ...result });
  } catch (err) {
    if (
      err instanceof AuthRequiredError ||
      err instanceof ForbiddenError ||
      err instanceof CsrfError
    ) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    const message = err instanceof Error ? err.message : "approve failed";
    const status = message.includes("conflict") ? 409 : 400;
    return NextResponse.json({ error: message }, { status });
  }
}
