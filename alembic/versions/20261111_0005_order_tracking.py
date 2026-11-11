"""Order tracking: realistic laundry stages and an append-only status history.

- Allow PICKED_UP, CLEANING and READY between ACCEPTED and DELIVERING.
- ``order_status_events`` records every status an order entered, when, and who
  moved it there. It is written in the same transaction as the status change.
- Existing orders get history rows reconstructed from their timestamps.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-11
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

OLD_STATUSES = ("PENDING", "ACCEPTED", "DELIVERING", "COMPLETED", "CANCELLED")
NEW_STATUSES = (
    "PENDING", "ACCEPTED", "PICKED_UP", "CLEANING", "READY", "DELIVERING", "COMPLETED", "CANCELLED",
)


def _status_check(column: str, statuses: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(s) for s in statuses)})"


def upgrade() -> None:
    op.drop_constraint("ck_orders_status", "orders", type_="check")
    op.create_check_constraint("ck_orders_status", "orders", _status_check("status", NEW_STATUSES))

    op.create_table(
        "order_status_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(_status_check("status", NEW_STATUSES), name="ck_order_status_events_status"),
    )
    op.create_index("ix_order_status_events_order", "order_status_events", ["order_id", "created_at"])

    # Reconstruct what the timestamps can tell us about pre-existing orders.
    op.execute(
        """
        INSERT INTO order_status_events (order_id, status, actor_id, created_at)
        SELECT id, 'PENDING', customer_id, created_at FROM orders
        UNION ALL
        SELECT id, 'ACCEPTED', NULL, accepted_at FROM orders WHERE accepted_at IS NOT NULL
        UNION ALL
        SELECT id, 'COMPLETED', NULL, completed_at FROM orders WHERE completed_at IS NOT NULL
        UNION ALL
        SELECT id, 'CANCELLED', NULL, cancelled_at FROM orders WHERE cancelled_at IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_table("order_status_events")
    op.execute("UPDATE orders SET status = 'ACCEPTED' WHERE status IN ('PICKED_UP', 'CLEANING', 'READY')")
    op.drop_constraint("ck_orders_status", "orders", type_="check")
    op.create_check_constraint("ck_orders_status", "orders", _status_check("status", OLD_STATUSES))
