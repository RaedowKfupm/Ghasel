BEGIN;

-- The new lifecycle omits READY; map existing ready orders to DELIVERING.
UPDATE orders
SET status = 'DELIVERING'
WHERE upper(status) = 'READY';

-- Deletion belongs to the customer/branch lifecycle, not to an individual order.
ALTER TABLE orders DROP COLUMN IF EXISTS is_deleted;
ALTER TABLE orders DROP COLUMN IF EXISTS deleted_at;

COMMIT;
