# Stage B — Date semantics

**Conclusion:** `VERSION_TO_VERSION_COMPARATOR_ONLY`

## Rationale

Filename version datetime and meta/dc:date reliably identify the whole-instrument open-data XML snapshot. Section @startPeriod is explicit but not safely mapped in this spike to a user-facing 'law in force on date X' promise. Narrative commencementNote is instrument-level only. Therefore the supported product promise is a version-to-version comparator (optionally labeled with source_version_datetime), not an as-at-date force-of-law query.

## Field findings

| Field | Value (sample) | Applies to | Explicit | Confidence | May use in UI |
|-------|----------------|------------|----------|------------|---------------|
| `download_datetime` | None | acquisition | True | high | True |
| `source_version_datetime` | 20110630000000 | instrument | True | high | True |
| `whole_instrument_version_date` | 20110630000000 | instrument | True | medium | True |
| `dc_date_instrument_meta` | 2011-06-30 | instrument | True | high | True |
| `provision_start_period` | 2011-06-30 | provision | True | medium | False |
| `provision_last_updated_date` | None | provision | False | none | False |
| `effective_date` | None | provision | False | none | False |
| `commencement_date` | None | instrument | True | medium | False |

### Notes per field

- **download_datetime** (import_run / source_registry.download_timestamp): Acquisition timestamp only; never a legal version date.
- **source_version_datetime** (filename pattern ..._[yyyymmddhhmiss]_[lang]_[c|p].xml): Official data dictionary documents this as Version date for the XML resource. It is a whole-file version timestamp, not proven as provision commencement.
- **whole_instrument_version_date** (same as filename version date unless a distinct meta property is found): Treated as equivalent to source_version_datetime for these fixtures unless meta properties provide a different instrument version date.
- **dc_date_instrument_meta** (meta/dc:date (Dublin Core) in instrument XML): Observed to align with filename version date (YYYY-MM-DD vs yyyymmddhhmiss). Treat as instrument snapshot/version date metadata, not provision commencement.
- **provision_start_period** (section/@startPeriod (and optionally @endPeriod)): Explicit attribute present on many Cap. 614 sections. Attribute name is startPeriod, not effective_date or commencement_date. Without an authoritative mapping from the data dictionary/XSD semantics into a user-facing 'law in force on date X' promise, do not use this field for that claim in Stage B.
- **provision_last_updated_date** (no dedicated last-updated field distinct from startPeriod observed): Do not infer from instrument version date or startPeriod.
- **effective_date** (no attribute literally named effective date on Cap. 614 sections): Must not relabel filename version date or startPeriod as effective_date without source documentation proving equivalence.
- **commencement_date** (commencementNote narrative (e.g. '[30 June 2011]') at instrument level): Narrative commencementNote exists for Cap. 614 but is not a structured per-section commencement date suitable for as-at queries in Stage B.

Observed date-like doc property keys: `['element:dc:date', 'element:docStatus']`

`startPeriod` coverage on Cap. 614 section versions: **343/429**
