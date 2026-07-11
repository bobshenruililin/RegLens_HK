-- MVP-RC2: allow pending queue rows without a human reviewer yet;
-- expand review_status to match the Studio control plane.

ALTER TABLE reviews
    ALTER COLUMN reviewer_user_id DROP NOT NULL;

ALTER TABLE reviews
    DROP CONSTRAINT IF EXISTS reviews_status_check;

ALTER TABLE reviews
    ADD CONSTRAINT reviews_status_check CHECK (
        review_status IN (
            'pending',
            'accepted',
            'edited',
            'rejected',
            'disputed',
            'incomplete'
        )
    );

ALTER TABLE reviews
    DROP CONSTRAINT IF EXISTS reviews_pending_reviewer_null_check;

ALTER TABLE reviews
    ADD CONSTRAINT reviews_pending_reviewer_null_check CHECK (
        (review_status = 'pending' AND reviewer_user_id IS NULL)
        OR (review_status <> 'pending' AND reviewer_user_id IS NOT NULL)
    );

COMMENT ON COLUMN reviews.reviewer_user_id IS
    'Human reviewer for terminal review actions. NULL only while review_status=pending '
    '(ingest queue placeholder).';

-- Extraction run lifecycle: queued before a worker starts processing.
ALTER TABLE extraction_runs
    DROP CONSTRAINT IF EXISTS extraction_runs_status_check;

ALTER TABLE extraction_runs
    ADD CONSTRAINT extraction_runs_status_check CHECK (
        status IN ('queued', 'running', 'succeeded', 'failed', 'quarantined')
    );
