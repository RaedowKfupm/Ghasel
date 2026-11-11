BEGIN;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS laundry_id INTEGER
    REFERENCES "Laundry" (id) ON DELETE SET NULL;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS laundry_branch_id INTEGER
    REFERENCES "Branches" (id) ON DELETE SET NULL;

-- Move the existing laundry owner link onto the user row.
UPDATE users AS u
SET laundry_id = l.id
FROM "Laundry" AS l
WHERE l.owner_id = u.id
  AND u.laundry_id IS NULL;

-- Preserve branch assignments from the old branch-to-manager column.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'Branches'
          AND column_name = 'manager_id'
    ) THEN
        EXECUTE 'UPDATE users AS u
                 SET laundry_branch_id = b.id
                 FROM "Branches" AS b
                 WHERE b.manager_id = u.id
                   AND u.laundry_branch_id IS NULL';
    END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM users
    WHERE lower(role) IN ('manager', 'operator')
      AND laundry_branch_id IS NULL
  ) THEN
    RAISE EXCEPTION 'Assign every existing manager/operator to a branch before applying this migration';
  END IF;
END $$;

ALTER TABLE "Branches" DROP COLUMN IF EXISTS manager_id;
ALTER TABLE "Laundry" DROP COLUMN IF EXISTS owner_id;
DROP TABLE IF EXISTS laundry_managers;

COMMIT;
