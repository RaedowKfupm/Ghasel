"""Repair drift between the SQLAlchemy models and the database.

- Create ``laundry_requests``, which existed in the models but never in the database.
- Give each laundry company its own ``name`` (previously only on the request row).
- Normalise legacy lower-case role values and enforce NOT NULL / allowed roles.
- Store timestamps as timestamptz, with ``created_at`` defaulting to ``now()``.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

USER_ROLES = ("CUSTOMER", "LAUNDRY", "ADMIN", "MANAGER")
REQUEST_STATUSES = ("PENDING", "APPROVED", "REJECTED")
TIMESTAMP_COLUMNS = (
    ("Laundry", "created_at"),
    ("Branches", "created_at"),
    ("laundry_requests", "created_at"),
    ("laundry_requests", "decided_at"),
    ("orders", "created_at"),
    ("orders", "accepted_at"),
    ("orders", "completed_at"),
)


def _in_list(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def upgrade() -> None:
    op.create_table(
        "laundry_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("decided_at", sa.DateTime()),
        sa.Column(
            "laundry_id",
            sa.Integer(),
            sa.ForeignKey("Laundry.id", ondelete="SET NULL"),
        ),
        sa.CheckConstraint(
            _in_list("status", REQUEST_STATUSES), name="ck_laundry_requests_status"
        ),
    )
    # The service already rejects a second pending application; enforce it in the database too.
    op.create_index(
        "uq_laundry_requests_one_pending_per_owner",
        "laundry_requests",
        ["owner_id"],
        unique=True,
        postgresql_where=sa.text("status = 'PENDING'"),
    )

    op.add_column("Laundry", sa.Column("name", sa.String()))
    op.execute(
        """
        UPDATE "Laundry" AS l
        SET name = r.company_name
        FROM laundry_requests AS r
        WHERE r.laundry_id = l.id AND l.name IS NULL
        """
    )
    op.execute("""UPDATE "Laundry" SET name = 'Laundry #' || id WHERE name IS NULL""")
    op.alter_column("Laundry", "name", nullable=False)

    # SQLAlchemy stores enum *names*; early rows were written with values ('customer').
    op.execute("UPDATE users SET role = upper(role) WHERE role <> upper(role)")
    for column in ("name", "email", "password_hash", "role"):
        op.alter_column("users", column, nullable=False)
    op.create_check_constraint("ck_users_role", "users", _in_list("role", USER_ROLES))

    # Naive timestamps were written as UTC; store them as timestamptz from now on.
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
        if column == "created_at":
            op.alter_column(table, column, server_default=sa.func.now())


def downgrade() -> None:
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(table, column, server_default=None)
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
    op.drop_constraint("ck_users_role", "users", type_="check")
    for column in ("name", "email", "password_hash", "role"):
        op.alter_column("users", column, nullable=True)
    op.drop_column("Laundry", "name")
    op.drop_table("laundry_requests")
