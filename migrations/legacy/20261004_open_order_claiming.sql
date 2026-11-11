BEGIN;

-- Open marketplace orders have no assigned branch until an operator claims them.
ALTER TABLE orders ALTER COLUMN branch_id DROP NOT NULL;

COMMIT;
