"""Publication and review helpers (Milestone 2C)."""

from __future__ import annotations

from typing import Any

from .contracts import can_publish_proposition
from .privacy import redact_derived_text
from .store import LocalArtifactStore, utc_now_iso


class PublicationError(ValueError):
    pass


def set_proposition_review(
    store: LocalArtifactStore,
    *,
    decision_id: str,
    proposition_id: str,
    review_status: str,
    claim_text: str | None = None,
    publish: bool | None = None,
) -> dict[str, Any]:
    decision = store.get_decision(decision_id)
    if not decision:
        raise PublicationError(f"Decision not found: {decision_id}")

    found = None
    for prop in decision["propositions"]:
        if prop["id"] == proposition_id:
            found = prop
            break
    if not found:
        raise PublicationError(f"Proposition not found: {proposition_id}")

    if claim_text is not None:
        found["claim_text"] = redact_derived_text(claim_text)
        if review_status == "accepted":
            review_status = "edited"

    found["review_status"] = review_status
    if publish is None:
        should_publish = review_status in {"accepted", "edited"}
    else:
        should_publish = publish

    if should_publish:
        if not can_publish_proposition(
            review_status=found["review_status"], evidence=found.get("evidence") or []
        ):
            raise PublicationError(
                "Cannot publish without review accept/edit and at least one evidence span"
            )
        found["published"] = True
    else:
        found["published"] = False

    decision["generated_at"] = utc_now_iso()
    store.save_decision(decision)
    return decision


def pending_review_queue(store: LocalArtifactStore) -> list[dict[str, Any]]:
    items = []
    for decision in store.list_decisions():
        for prop in decision.get("propositions", []):
            if prop.get("review_status") == "pending" or (
                not prop.get("published") and prop.get("review_status") != "rejected"
            ):
                if prop.get("review_status") == "rejected":
                    continue
                if prop.get("published"):
                    continue
                items.append(
                    {
                        "decision_id": decision["id"],
                        "decision_title": decision.get("title"),
                        "regulator_code": decision.get("regulator_code"),
                        "proposition": prop,
                    }
                )
    return items
