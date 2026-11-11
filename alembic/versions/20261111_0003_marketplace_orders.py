"""Marketplace orders: unassigned PENDING orders that branches compete to accept.

- Fold the legacy OPEN status into PENDING (an unassigned PENDING order is on
  the marketplace; one with a branch is a direct request to that branch).
- Constrain status values and require a branch once an order leaves PENDING.
- Record cancellation time and index the order feeds.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-11
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

ORDER_STATUSES = ("PENDING", "ACCEPTED", "DELIVERING", "COMPLETED", "CANCELLED")


def upgrade() -> None:
    op.execute("UPDATE orders SET status = 'PENDING' WHERE status = 'OPEN'")
    op.add_column("orders", sa.Column("cancelled_at", sa.DateTime(timezone=True)))

    op.create_check_constraint(
        "ck_orders_status",
        "orders",
        "status IN ({})".format(", ".join(f"'{s}'" for s in ORDER_STATUSES)),
    )
    # A customer may cancel an unassigned order, so only PENDING/CANCELLED may lack a branch.
    op.create_check_constraint(
        "ck_orders_branch_assigned",
        "orders",
        "branch_id IS NOT NULL OR status IN ('PENDING', 'CANCELLED')",
    )

    op.create_index("ix_orders_customer_created", "orders", ["customer_id", sa.text("created_at DESC")])
    op.create_index("ix_orders_branch_created", "orders", ["branch_id", sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_index("ix_orders_branch_created", "orders")
    op.drop_index("ix_orders_customer_created", "orders")
    op.drop_constraint("ck_orders_branch_assigned", "orders", type_="check")
    op.drop_constraint("ck_orders_status", "orders", type_="check")
    op.drop_column("orders", "cancelled_at")
    op.execute("UPDATE orders SET status = 'OPEN' WHERE status = 'PENDING' AND branch_id IS NULL")
