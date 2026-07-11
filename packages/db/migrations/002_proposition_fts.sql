-- Milestone 2D: FTS on published proposition claims
ALTER TABLE propositions
  ADD COLUMN IF NOT EXISTS claim_tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('english', coalesce(claim_text, ''))) STORED;

CREATE INDEX IF NOT EXISTS propositions_claim_tsv_idx
  ON propositions USING GIN (claim_tsv);
