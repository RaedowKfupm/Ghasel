"""Geospatial discovery: branch locations, service radius and order pickup points.

Latitude/longitude are the source of truth (validated by CHECK constraints);
a STORED generated ``geography(Point, 4326)`` column derived from them is what
the GiST indexes and ``ST_DWithin`` / ``ST_Distance`` queries use, so the two
can never disagree.

Existing branches keep NULL coordinates: they are simply excluded from nearby
search and from the marketplace until a location is set.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-11
"""
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def point_from(lat: str, lng: str) -> str:
    return (
        f"CASE WHEN {lat} IS NOT NULL AND {lng} IS NOT NULL "
        f"THEN ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography END"
    )


def coordinate_checks(table: str, lat: str, lng: str, prefix: str) -> None:
    op.create_check_constraint(f"ck_{prefix}_latitude", table, f"{lat} BETWEEN -90 AND 90")
    op.create_check_constraint(f"ck_{prefix}_longitude", table, f"{lng} BETWEEN -180 AND 180")
    op.create_check_constraint(
        f"ck_{prefix}_coordinates_paired", table, f"({lat} IS NULL) = ({lng} IS NULL)"
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # --- Branches -----------------------------------------------------------
    op.add_column("Branches", sa.Column("latitude", sa.Float()))
    op.add_column("Branches", sa.Column("longitude", sa.Float()))
    op.add_column(
        "Branches",
        sa.Column("service_radius_km", sa.Float(), nullable=False, server_default="10"),
    )
    op.add_column(
        "Branches",
        sa.Column(
            "location",
            Geography("POINT", srid=4326, spatial_index=False),
            sa.Computed(point_from("latitude", "longitude"), persisted=True),
        ),
    )
    coordinate_checks("Branches", "latitude", "longitude", "branches")
    op.create_check_constraint(
        "ck_branches_service_radius", "Branches", "service_radius_km > 0 AND service_radius_km <= 100"
    )
    op.create_index("ix_branches_location", "Branches", ["location"], postgresql_using="gist")

    # --- Orders ---------------------------------------------------------------
    op.add_column("orders", sa.Column("pickup_address", sa.String()))
    op.add_column("orders", sa.Column("pickup_latitude", sa.Float()))
    op.add_column("orders", sa.Column("pickup_longitude", sa.Float()))
    op.add_column(
        "orders",
        sa.Column(
            "pickup_location",
            Geography("POINT", srid=4326, spatial_index=False),
            sa.Computed(point_from("pickup_latitude", "pickup_longitude"), persisted=True),
        ),
    )
    coordinate_checks("orders", "pickup_latitude", "pickup_longitude", "orders_pickup")
    # Marketplace orders are matched to branches by distance, so they need a pickup point.
    op.create_check_constraint(
        "ck_orders_marketplace_has_pickup",
        "orders",
        "branch_id IS NOT NULL OR status = 'CANCELLED' OR pickup_latitude IS NOT NULL",
    )
    op.create_index(
        "ix_orders_marketplace_pickup",
        "orders",
        ["pickup_location"],
        postgresql_using="gist",
        postgresql_where=sa.text("status = 'PENDING' AND branch_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_orders_marketplace_pickup", "orders")
    for name in ("marketplace_has_pickup", "pickup_coordinates_paired", "pickup_longitude", "pickup_latitude"):
        op.drop_constraint(f"ck_orders_{name}", "orders", type_="check")
    for column in ("pickup_location", "pickup_longitude", "pickup_latitude", "pickup_address"):
        op.drop_column("orders", column)

    op.drop_index("ix_branches_location", "Branches")
    for name in ("service_radius", "coordinates_paired", "longitude", "latitude"):
        op.drop_constraint(f"ck_branches_{name}", "Branches", type_="check")
    for column in ("location", "service_radius_km", "longitude", "latitude"):
        op.drop_column("Branches", column)
