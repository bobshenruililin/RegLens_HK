# Source and licensing audit

**Gate:** Do not build public pages that reproduce substantial judgment text until
`consent_status=granted` **or** the product remains strictly internal and the UI
shows only short cited quotes under fair-dealing advice from counsel
(counsel sign-off required).

## Audit template (one row / section per collection)

| Field | Guidance |
|-------|----------|
| `source_id` | Stable id, e.g. `mchk_judgments` |
| `regulator` | Official body name |
| `collection_name` | Human-readable collection |
| `official_index_url` | Canonical index URL |
| `document_types` | PDF / HTML / Gazette, etc. |
| `coverage_policy` | What the publisher says is included |
| `copyright_owner` | Council / HKSAR Government / other |
| `copyright_notice_url` | Link to notice |
| `permitted_uses` | Quote exact licence text for personal/internal use |
| `prohibited_uses` | Sale, commercial benefit, advertising, moral-rights violations |
| `attribution_required` | Usually yes |
| `commercial_consent_required` | Yes for commercial product (MCHK cl.7) |
| `consent_contact` | Email / channel |
| `consent_status` | `not_requested` / `requested` / `granted` / `refused` / `withdrawn` |
| `robots_txt_url` | URL + fetch date (even though MVP is manual) |
| `terms_reviewed_by` | Name + date |
| `pii_profile` | Practitioner vs patient / third-party risk |
| `retention_policy` | Immutable raw; derived under licence terms |
| `takedown_process` | Owner request → unpublish; retain audit log |
| `fixture_acquisition_method` | Manual browser download by named operator |
| `hash_manifest` | Path to manifest JSONL |
| `risk_rating` | Low / Medium / High |
| `mvp_allowed` | True only if internal-use path **or** consent granted |

---

## Completed row: `mchk_judgments`

| Field | Value |
|-------|-------|
| source_id | mchk_judgments |
| regulator | Medical Council of Hong Kong |
| collection_name | Judgments of disciplinary inquiries |
| official_index_url | https://www.mchk.org.hk/english/complaint/disciplinary.php?type=j |
| document_types | PDF judgments; HTML index pages |
| coverage_policy | Judgments on/after 2 Jul 2008 where the Council’s order is gazetted |
| copyright_owner | Medical Council of Hong Kong |
| copyright_notice_url | https://www.mchk.org.hk/english/important_notices/important_notices.html |
| permitted_uses | Council copyright-protected **text** may be reproduced and distributed free of charge for **personal or internal use within an organisation**, accurately, with attribution, and **not** for sale or commercial purposes (Copyright Notice cl.5). |
| prohibited_uses | Any use other than cl.5 (including commercial purposes listed in the notice) without prior written consent (cl.7); non-text contents without consent (cl.3). |
| attribution_required | Yes — acknowledge the Council as copyright owner and source |
| commercial_consent_required | **Yes** |
| consent_contact | mchk@dh.gov.hk |
| consent_status | `not_requested` — updated RC3 draft ready (`licensing/MCHK_CONSENT_REQUEST.md`); human must send; public real releases remain blocked |
| robots_txt_url | https://www.mchk.org.hk/robots.txt (record fetch date when reviewed operationally) |
| terms_reviewed_by | Phase 0 package / 2026-07-11 |
| pii_profile | Practitioner names public; patients often redacted (e.g. Madam/Mr xxx); residual risk remains |
| retention_policy | Keep immutable raw; publish only derived structured data under licence posture |
| takedown_process | Owner request → unpublish within 1 business day; retain audit log |
| fixture_acquisition_method | Synthetic fixtures in-repo for engineering; real docs only via `scripts/download_checklist.md` |
| hash_manifest | `fixtures/manifests/m1.jsonl` |
| risk_rating | High (commercial public product) / Medium (internal tooling) |
| mvp_allowed | **true** for internal posture only |

---

## Completed row: `dchk_judgments`

| Field | Value |
|-------|-------|
| source_id | dchk_judgments |
| regulator | Dental Council of Hong Kong |
| collection_name | Judgments of disciplinary inquiries |
| official_index_url | https://www.dchk.org.hk/en/complaints_disciplinary/judgments.html |
| document_types | PDF judgments |
| coverage_policy | On/after 17 Sep 2009; from 14 Jul 2018 the Council publishes written judgments where all/some charges were found guilty |
| copyright_owner | Confirm on DCHK site notice / related HKSAR notices (treat as restricted until confirmed) |
| copyright_notice_url | Confirm on official site at terms-review time |
| permitted_uses | Treat as **internal-use only** until confirmed in writing |
| prohibited_uses | Commercial republication without consent |
| attribution_required | Yes |
| commercial_consent_required | **Yes** (assumed until confirmed otherwise) |
| consent_contact | Dental Council secretariat / official site contact channels |
| consent_status | `not_requested` — updated RC3 draft ready (`licensing/DCHK_CONSENT_REQUEST.md`); human must send; public real releases remain blocked |
| robots_txt_url | Record when reviewed |
| terms_reviewed_by | Phase 0 package / 2026-07-11 |
| pii_profile | Similar to MCHK |
| retention_policy | Same as MCHK row |
| takedown_process | Same as MCHK row |
| fixture_acquisition_method | Synthetic + manual checklist only |
| hash_manifest | `fixtures/manifests/m1.jsonl` |
| risk_rating | High (commercial) / Medium (internal) |
| mvp_allowed | **true** for internal posture only |

---

## Deferred: `nchk_judgments`

Not in MVP. Do not ingest NCHK materials until a completed audit row sets `mvp_allowed=true`.

## Outreach

See [`licensing/OUTREACH_LOG.md`](licensing/OUTREACH_LOG.md).

---

## Enforcement via `source_publication_policy` (MVP-RC1)

Licensing posture is enforced in the **publication release builder**, not by
rewriting this audit’s consent fields.

Machine-readable policy:
[`publications/policies/source_publication_policy.v1.json`](../publications/policies/source_publication_policy.v1.json)
(schema: [`publications/schemas/source_publication_policy.v1.json`](../publications/schemas/source_publication_policy.v1.json)).

| Mechanism | Behaviour |
|-----------|-----------|
| `visibility: internal_only` | `release_mode=public` **refuses** inclusion of that source |
| `max_excerpt_chars` | Caps public evidence excerpts |
| `attribution_required` | Requires attribution strings on public decisions |
| `synthetic_demo` | Allows synthetic fixtures only; treats them as demo `public_excerpt` without changing real-source consent |

**Do not change `consent_status` values in this audit** to “unlock” engineering
demos. Consent rows remain the human/legal record (`not_requested` until
outreach progresses). Flipping policy visibility is a separate, deliberate
licensing decision recorded with counsel and outreach updates — not a CI
convenience.

Until MCHK/DCHK leave `internal_only`, GitHub Pages must ship only
`synthetic_demo` (or an empty/blocked public build). Real public republication
remains blocked by source policy.
