# Editorial handbook (RC4)

This handbook is the working codebook for RegLens HK editorial review. All
examples below are **synthetic** and are not real regulatory decisions. Do not
copy language from real judgments into this file.

## Coding principles

1. Code only propositions supported by evidence spans.
2. Preserve the distinction between facts and interpretation through
   `epistemic_class`.
3. Prefer narrow, auditable claims over broad summaries.
4. Use `derivation` consistently:
   - `verbatim` - copied from the source excerpt, with redaction if needed.
   - `normalized` - source wording restated into a structured field.
   - `inferred` - reviewer interpretation from supported spans.
5. Record uncertainty instead of forcing a category.

## Proposition codebook

| Code | Use for | Do not use for | Synthetic example |
|------|---------|----------------|-------------------|
| `decision` | Stable identity and source-level metadata for one disciplinary outcome. | A proposition inside the decision. | `Synthetic MCHK decision SYN-MCHK-2024-001`, regulator `MCHK`, profession `doctor`, year `2024`. |
| `charge` | The allegation or complaint the tribunal resolves. | Background conduct not framed as a charge. | "Failed to keep adequate clinical records for a synthetic patient." |
| `finding` | Whether a charge is proved, admitted, dismissed, or otherwise resolved. | Sanction reasoning or mitigation. | "The synthetic charge was admitted and found proved." |
| `sanction` | Orders, penalties, warnings, costs, suspension/removal terms, or no-order results. | The finding that misconduct occurred. | "A warning letter is ordered; no costs order is made." |
| `factor` | Mitigating, aggravating, neutral, or contextual factors used in reasoning. | A standalone sanction. | "The practitioner had a clear prior synthetic disciplinary record." |
| `authority` | Cases, statutes, rules, or legal tests cited as authority. | Free-form issue tags. | "Synthetic Professional Conduct Code section 4.2 is cited for recordkeeping." |
| `takeaway` | Human-authored editorial synthesis for a public decision page or internal report. | New legal propositions unsupported by coded evidence. | "In this synthetic example, admitted recordkeeping failures still support a formal warning." |
| `uncertainty` | Known ambiguity, missing evidence, or reviewer doubt. | A substitute for review. | "The synthetic fixture does not state whether an appeal was lodged." |

## Field guidance

### Decision

Required review checks:

- `public_id` is stable and release-scoped.
- `slug` is URL-safe.
- `regulator_code` is one of the MVP regulators.
- `fixture_kind` is `synthetic` for demo publication.

Synthetic example:

```json
{
  "slug": "syn-mchk-2024-001",
  "regulator_code": "MCHK",
  "profession": "doctor",
  "fixture_kind": "synthetic"
}
```

### Charge

Capture the allegation as specifically as the evidence permits. If a charge has
multiple limbs, split only when the source resolves limbs separately.

Synthetic example:

> The synthetic practitioner failed to keep adequate clinical records for
> [REDACTED_PERSON].

Coding:

- `prop_type`: `charge`
- `epistemic_class`: `fact`
- `derivation`: `normalized`

### Finding

Code the outcome separately from the charge text.

Synthetic examples:

- `proved`
- `admitted`
- `not_proved`
- `partly_proved`
- `withdrawn`

If the finding is not explicit, add an `uncertainty` note rather than guessing.

### Sanction

Record both category tags and the order wording where available.

Synthetic examples:

- `warning`
- `costs`
- `removal_suspended`
- `no_order`

Do not normalize a warning into suspension/removal language unless the evidence
uses that order.

### Factor

Use factor coding for facts the decision uses in reasoning.

Synthetic examples:

| Polarity | Example |
|----------|---------|
| Mitigating | "Clear prior synthetic record." |
| Aggravating | "Repeated synthetic non-compliance after advice." |
| Neutral/context | "The synthetic conduct occurred during a clinic transition." |

### Authority

Authority propositions are not endorsements by RegLens. They record that the
decision cited or applied an authority.

Synthetic example:

```json
{
  "prop_type": "authority",
  "claim_text": "Synthetic Council v Example Practitioner is cited for sanction proportionality.",
  "structured": {
    "citation": "Synthetic Council v Example Practitioner"
  }
}
```

### Takeaway

Takeaways are editorial interpretation, not source text. They must:

- be concise;
- avoid legal advice;
- refer to coded facts instead of adding new facts;
- disclose synthetic/demo status when used in public examples.

Synthetic example:

> For demo purposes, admitted recordkeeping failures can still be represented as
> a formal warning outcome where the synthetic decision records no costs order.

### Uncertainty

Use uncertainty when evidence is missing, ambiguous, contradictory, or outside
scope.

Synthetic examples:

- "The synthetic fixture does not state whether appeal time expired."
- "The sanction date is not stated separately from the inquiry date."
- "The source excerpt supports a recordkeeping issue but not a prescribing issue."

Uncertainty should remain visible to reviewers and must not be silently dropped
from internal reports.
