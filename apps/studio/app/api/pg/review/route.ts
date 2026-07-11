import { NextResponse } from "next/server";
import {
  AuthRequiredError,
  CsrfError,
  ForbiddenError,
  assertMutationSafe,
  requireRole,
} from "../../../../lib/auth-server";
import { isDemoMode, isPostgresMode } from "../../../../lib/mode";
import { submitReviewAction } from "../../../../lib/pg-data";

export async function POST(req: Request) {
  if (!isPostgresMode()) {
    return NextResponse.json(
      {
        error: "postgres mode required",
        hint: "Use /api/review in demo mode (REGLENS_MODE=demo)",
      },
      { status: 400 }
    );
  }
  try {
    const body = (await req.json()) as {
      extracted_proposition_id?: string;
      review_status?: "accepted" | "edited" | "rejected";
      claim_text?: string;
      expected_head_revision_number?: number;
      notes?: string;
      csrf?: string;
    };
    await assertMutationSafe(req, body.csrf);
    const user = await requireRole("reviewer");

    if (
      !body.extracted_proposition_id ||
      !body.review_status ||
      body.expected_head_revision_number == null
    ) {
      return NextResponse.json(
        {
          error:
            "extracted_proposition_id, review_status, expected_head_revision_number required",
        },
        { status: 400 }
      );
    }

    const result = await submitReviewAction({
      extractedPropositionId: body.extracted_proposition_id,
      reviewerUserId: user.id,
      reviewStatus: body.review_status,
      claimText: body.claim_text,
      expectedHeadRevisionNumber: body.expected_head_revision_number,
      notes: body.notes,
    });

    return NextResponse.json({ ok: true, ...result });
  } catch (err) {
    if (
      err instanceof AuthRequiredError ||
      err instanceof ForbiddenError ||
      err instanceof CsrfError
    ) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    const message = err instanceof Error ? err.message : "review failed";
    const status = message.includes("conflict") ? 409 : 400;
    return NextResponse.json({ error: message }, { status });
  }
}

export async function GET() {
  if (isDemoMode()) {
    return NextResponse.json({
      error: "Use /api/review in demo mode",
      mode: "demo",
    });
  }
  return NextResponse.json({
    mode: "postgres",
    notice: "POST review actions to this endpoint",
  });
}
