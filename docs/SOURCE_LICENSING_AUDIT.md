# Source and licensing audit

Complete one section per collection before redistribution beyond the team.

## Template fields

`source_id`, `regulator`, `collection_name`, `official_index_url`, `document_types`,
`coverage_policy`, `copyright_owner`, `copyright_notice_url`, `permitted_uses`,
`prohibited_uses`, `attribution_required`, `commercial_consent_required`,
`consent_contact`, `consent_status`, `robots_txt_url`, `terms_reviewed_by`,
`pii_profile`, `retention_policy`, `takedown_process`, `fixture_acquisition_method`,
`hash_manifest`, `risk_rating`, `mvp_allowed`.

---

## mchk_judgments

| Field | Value |
|-------|-------|
| source_id | mchk_judgments |
| regulator | Medical Council of Hong Kong |
| collection_name | Judgments of disciplinary inquiries |
| official_index_url | https://www.mchk.org.hk/english/complaint/disciplinary.php?type=j |
| document_types | PDF judgments; HTML index |
| coverage_policy | Judgments on/after 2 Jul 2008 where order gazetted |
| copyright_owner | Medical Council of Hong Kong |
| copyright_notice_url | https://www.mchk.org.hk/english/important_notices/important_notices.html |
| permitted_uses | Personal or internal organisational use of Council text; accurate reproduction; attribution |
| prohibited_uses | Sale / commercial benefit / advertising without prior written consent |
| attribution_required | Yes |
| commercial_consent_required | Yes |
| consent_contact | mchk@dh.gov.hk |
| consent_status | not_requested (letter drafted — see `docs/licensing/`) |
| robots_txt_url | https://www.mchk.org.hk/robots.txt (record fetch date when reviewed) |
| terms_reviewed_by | Phase 0 package / 2026-07-11 |
| pii_profile | Practitioner names public; patients often redacted; residual risk |
| retention_policy | Immutable raw fixtures; derived fields minimised |
| takedown_process | Unpublish within 1 business day of owner request; retain audit log |
| fixture_acquisition_method | Synthetic fixtures in-repo; real docs via manual checklist only |
| hash_manifest | fixtures/manifests/m1.jsonl |
| risk_rating | High (commercial) / Medium (internal) |
| mvp_allowed | true for **internal** synthetic + internal-use real fixtures only |

## dchk_judgments

| Field | Value |
|-------|-------|
| source_id | dchk_judgments |
| regulator | Dental Council of Hong Kong |
| collection_name | Judgments of disciplinary inquiries |
| official_index_url | https://www.dchk.org.hk/en/complaints_disciplinary/judgments.html |
| document_types | PDF judgments |
| coverage_policy | On/after 17 Sep 2009; from Jul 2018 guilty (all/some charges) only |
| copyright_owner | Confirm on DCHK site notice / related HKSAR notices |
| copyright_notice_url | Confirm on official site |
| permitted_uses | Treat as internal-use only until confirmed |
| prohibited_uses | Commercial republication without consent |
| attribution_required | Yes |
| commercial_consent_required | Yes (assumed until confirmed otherwise) |
| consent_contact | Via Dental Council secretariat / site contact channels |
| consent_status | not_requested (letter drafted) |
| terms_reviewed_by | Phase 0 package / 2026-07-11 |
| pii_profile | Similar to MCHK |
| retention_policy | Same as MCHK |
| takedown_process | Same as MCHK |
| fixture_acquisition_method | Synthetic + manual only |
| hash_manifest | fixtures/manifests/m1.jsonl |
| risk_rating | High (commercial) / Medium (internal) |
| mvp_allowed | true for internal posture only |

**Gate:** No public pages reproducing substantial judgment text until
`consent_status=granted` or counsel signs off an internal-only short-quote UI.
