"""Customer reviews: at most one per order, rating 1-5.

The review references only its order; the branch and customer are the order's,
so they cannot drift apart. Branch ratings are aggregated from this table on
read rather than stored.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("order_id", name="uq_reviews_order"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
    )


def downgrade() -> None:
    op.drop_table("reviews")
