# RC3 source adapters

Source adapters convert regulator index HTML into normalized internal metadata.
They do not decide publication rights.

## Current adapters

| Source | Adapter | Purpose |
|--------|---------|---------|
| MCHK | `mchk_html_index` | Discover disciplinary judgment metadata from the official MCHK index. |
| DCHK | `dchk_html_table` | Discover judgment-table metadata and attach the DCHK coverage caveat. |

Adapters must emit stable source keys, case references, dates where available,
source/document URLs, parser health, and caveats. They must not embed raw PDFs,
full judgment text, or public-release decisions.

## Parser expectations

- Prefer deterministic HTML parsing over LLM interpretation.
- Fail closed when required markers disappear.
- Keep fixture tests offline under `fixtures/source_html/`.
- Record source caveats as metadata, not as legal conclusions.

## RC3 guardrails

- Public availability is not reuse permission.
- Robots directives are crawler signals, not licences.
- MCHK remains internal-only for public visibility.
- DCHK rows need the July 14, 2018 caveat: publication coverage is not complete.
- No real MCHK/DCHK content is released publicly in RC3.
- Do not claim complete de-identification.
- Student-research letters support the internal research posture only; they do
  not unlock Pages publication.
