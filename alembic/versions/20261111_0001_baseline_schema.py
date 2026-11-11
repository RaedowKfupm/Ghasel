"""Baseline: schema as produced by create_tables.py and the legacy SQL migrations.

Existing databases are stamped at this revision (``alembic stamp 0001``);
fresh databases are built from it.

Revision ID: 0001
Revises:
Create Date: 2026-11-11
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "Laundry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_Laundry_id", "Laundry", ["id"])

    op.create_table(
        "Branches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "laundry_id",
            sa.Integer(),
            sa.ForeignKey("Laundry.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("branch_name", sa.String()),
        sa.Column("branch_address", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_Branches_id", "Branches", ["id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String()),
        sa.Column("email", sa.String()),
        sa.Column("password_hash", sa.String()),
        sa.Column("role", sa.String()),
        sa.Column(
            "laundry_id",
            sa.Integer(),
            sa.ForeignKey("Laundry.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "laundry_branch_id",
            sa.Integer(),
            sa.ForeignKey("Branches.id", ondelete="SET NULL"),
        ),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "Customers",
        sa.Column(
            "id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("address", sa.String()),
    )
    op.create_index("ix_Customers_id", "Customers", ["id"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("branch_id", sa.Integer(), sa.ForeignKey("Branches.id")),
        sa.Column("details", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
    )
    op.create_index("ix_orders_id", "orders", ["id"])


def downgrade() -> None:
    for table in ("orders", "Customers", "users", "Branches", "Laundry"):
        op.drop_table(table)
