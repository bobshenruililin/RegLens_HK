# Stage B result

**Result:** FALLBACK (date) + PASS (identity)

## Date semantics
`VERSION_TO_VERSION_COMPARATOR_ONLY` — do not promise “law in force on date X”.

## Identity
- Precision on `@id` gold edges: **100%** (392 edges)
- Ordinary successor coverage: **100%** (392/392)
- Ambiguous: 0; unmatched old: 0; additions across history: 6

## XSD
Entrypoint `hklm.xsd` acquired from https://www.elegislation.gov.hk/schemas/hklm.xsd and SHA-256 matches published checksum.
Full offline validation blocked by unresolved external import closure (W3C/DC/XHTML/MathML outside allowlist).

## Recommended product promise after Stage B
Version-to-version comparator for Cap. 614 English top-level sections with stable `@id` lineage, labeled by `source_version_datetime` / `dc:date`, with mandatory informational disclaimer and HKeL verification links.
