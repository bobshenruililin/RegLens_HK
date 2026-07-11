# RC3 LLM processing

RC3 implements bounded extractor/critic plumbing, but real network LLM use is
not automatic. Deterministic parsing and schema validation remain preferred.

## Allowed default

- Mock/local provider in ordinary CI and demos.
- Bounded prompts with explicit source spans and schema output.
- Critic pass for consistency checks, not autonomous publication.
- Human review before acceptance.

## Real provider gate

Processing real text with a network LLM requires explicit runtime approval,
source-policy compatibility, privacy posture review, and no leakage to logs or
public artifacts. Model output starts pending/unpublished and must include
evidence spans.

## RC3 guardrails

- Public availability is not permission to send text to a provider or republish
  model-derived excerpts.
- robots.txt is not a licence.
- MCHK remains internal-only for public visibility.
- DCHK outputs need the July 14, 2018 source-coverage caveat where relevant.
- There is no RC3 public real release.
- No complete de-identification claim is made for prompts, outputs, or reviews.
- Student-research letters do not unlock Pages or public model-derived content.
