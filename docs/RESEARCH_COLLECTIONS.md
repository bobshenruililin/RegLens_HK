# Research collections (RC4)

Research collections define what a set of decisions is for, where it may live,
and which outputs are allowed.

## Collection types

| Collection | Source kind | Location | Public? | Purpose |
|------------|-------------|----------|---------|---------|
| Synthetic demo | Synthetic fixtures | Git + generated demo release | Yes, via Pages | Demonstrate pipeline and Observatory UX |
| Core10 | Real decisions when approved for internal handling; synthetic report fallback | Studio/private storage; synthetic reports in `reports/core10/` | No real data on Pages | Validate operations and reporting before Core50 |
| Core50 | Real decisions selected by pilot plan | Studio/private storage | No real data on Pages | Broader internal readiness pilot |
| Public real release | Real decisions | Publication release only after policy/legal/privacy approval | Future only | Public research dataset if approval changes |

## Core10 scope

Core10 is the next internal checkpoint. It should answer:

- Can metadata sync and acquisition be run with clear operator controls?
- Are charge/finding/sanction/factor/authority propositions reviewable?
- Where does uncertainty appear?
- What human interpretation is needed beyond structured counts?
- Which fields are required before Core50 scale?

Core10 is not a statistical sample and must not be presented as prevalence.

## Core50 scope

Core50 remains the internal scale-up target from ADR 0017:

- 25 planned MCHK records;
- 25 planned DCHK records;
- no source PDFs, OCR text, page text, or real public release artifacts in Git;
- human review required.

## Public release gate

A real public collection requires all of the following:

1. source-policy approval for public visibility;
2. legal/privacy approval for the release posture;
3. reviewed accepted/edited propositions only;
4. successful public scan;
5. updated Observatory copy that states coverage and caveats.

Until then, Pages may show synthetic demo artifacts and explanatory pages only.
