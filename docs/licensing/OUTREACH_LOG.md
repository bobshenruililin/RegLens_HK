# Licence outreach log

| Date | Body | Action | Channel | Status | Owner |
|------|------|--------|---------|--------|-------|
| 2026-07-11 | MCHK | Drafted consent request (RC1/Phase 0 wording) | `docs/licensing/MCHK_CONSENT_REQUEST.md` | superseded | — |
| 2026-07-11 | DCHK | Drafted consent request (RC1/Phase 0 wording) | `docs/licensing/DCHK_CONSENT_REQUEST.md` | superseded | — |
| 2026-07-11 | MCHK | Updated consent request (RC3 express asks) | `docs/licensing/MCHK_CONSENT_REQUEST.md` | superseded by postal grant below | — |
| 2026-07-11 | DCHK | Updated consent request (RC3 express asks) | `docs/licensing/DCHK_CONSENT_REQUEST.md` | superseded by postal grant below | — |
| 2026-07-11 | MCHK | **Owner reports written approval received by post** for use as an HKU Law student (also studying public health) | Postal letter (physical mail) | `granted_reported` — letter on file with owner; scan not yet in repo | Repository owner (Ruililin Shen) |
| 2026-07-11 | DCHK | **Owner reports written approval received by post** for the same student-research use | Postal letter (physical mail) | `granted_reported` — letter on file with owner; scan not yet in repo | Repository owner (Ruililin Shen) |

## Current legal posture (authoritative for operators)

1. **Internal / academic student research** with real MCHK and DCHK materials may proceed under the owner’s reported written postal approvals.
2. **Real public Observatory releases remain blocked** (`source_publication_policy` stays `internal_only`) until a human confirms the letters expressly allow the intended public surface (metadata / excerpts / derived facts) and updates policy with approval.
3. Do **not** assume the student-research letters automatically cover commercial products or full public republication.
4. Keep letter scans **out of Git**. Store under gitignored `private-data/licensing/` (or equivalent secure storage) and record the path in the audit only.

## Filing checklist (owner)

- [ ] Scan or photograph both postal letters (MCHK + DCHK)
- [ ] Store scans under `private-data/licensing/` (gitignored) — never commit them
- [ ] Note each letter’s date, reference number (if any), and the exact uses approved
- [ ] Confirm whether each letter covers: retrieval, internal storage, metadata, excerpts, derived facts, attribution, takedown, public non-profit, commercial
- [ ] Only after that review: decide whether any public-policy change is warranted (separate human/legal approval)

## Rules

1. Agents must not invent grant scope beyond what the owner reports or what a filed letter states.
2. `consent_status=granted` in the audit means **student / academic research use as reported**; it does **not** by itself unlock public Pages releases of real judgments.
3. Do **not** flip `source_publication_policy` visibility without an explicit human decision after reading the letters.
