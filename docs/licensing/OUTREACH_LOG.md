# Licence outreach log

| Date | Body | Action | Channel | Status | Owner |
|------|------|--------|---------|--------|-------|
| 2026-07-11 | MCHK | Drafted consent request (RC1/Phase 0 wording) | `docs/licensing/MCHK_CONSENT_REQUEST.md` → `mchk@dh.gov.hk` | superseded by RC3 update below | Human sender required |
| 2026-07-11 | DCHK | Drafted consent request (RC1/Phase 0 wording) | `docs/licensing/DCHK_CONSENT_REQUEST.md` → DCHK secretariat | superseded by RC3 update below | Human sender required |
| 2026-07-11 | MCHK | Updated consent request (RC3 express asks: retrieval, storage, metadata, excerpts, derived facts, attribution, takedown, non-profit vs commercial) | `docs/licensing/MCHK_CONSENT_REQUEST.md` → `mchk@dh.gov.hk` | `ready_to_send` | Human sender required |
| 2026-07-11 | DCHK | Updated consent request (same express asks) | `docs/licensing/DCHK_CONSENT_REQUEST.md` → DCHK official contact | `ready_to_send` | Human sender required |

## Rules

1. Outbound email must be sent by an authorised human using the organisation’s identity.
2. Agents must not invent a sender identity or mark status as `requested` / `sent` without evidence.
3. After send, update this log to `requested` with date, message-id/reference, and update the audit row (`consent_status`).
4. Real **public** releases remain **blocked** while source policy is `internal_only`, regardless of outreach status.
5. Internal MCHK pilot work may proceed under internal-use posture **without waiting** for replies; do not treat silence as public/commercial consent.

## Checklist before send

- [ ] Organisation letterhead / From address confirmed
- [ ] Legal reviewer approved wording
- [ ] Audit row contact and notice URLs re-checked on the live site
- [ ] DCHK “To:” address confirmed on the live site (do not guess)
- [ ] Placeholders filled: organisation name, contact, phone, date
- [ ] Internal-use / public-release-blocked posture still accurate in the letter
- [ ] After send: set outreach log to `requested` and audit `consent_status=requested`

## After replies

- Record grant / refusal / conditions per topic (retrieval, storage, metadata, excerpts, derived facts, attribution, takedown, non-profit, commercial).
- Do **not** flip `source_publication_policy` visibility without human/legal approval.
- Keep public real releases blocked until policy + consent expressly allow the intended public surface.
