"""PostGIS helpers shared by models and queries.

Points are WGS 84 (SRID 4326) ``geography`` values, so PostGIS measures
distances in metres along the spheroid rather than in planar degrees.
"""

from geoalchemy2 import Geography
from sqlalchemy import ColumnElement, Computed, cast, func

METRES_PER_KM = 1000


def GeographyPoint() -> Geography:  # noqa: N802 (reads like a column type)
    # Indexes are declared explicitly on the tables, so GeoAlchemy must not add its own.
    return Geography(geometry_type="POINT", srid=4326, spatial_index=False)


def generated_point(latitude: str, longitude: str) -> Computed:
    """A STORED point generated from a latitude/longitude column pair (NULL if either is NULL)."""
    return Computed(
        f"CASE WHEN {latitude} IS NOT NULL AND {longitude} IS NOT NULL "
        f"THEN ST_SetSRID(ST_MakePoint({longitude}, {latitude}), 4326)::geography END",
        persisted=True,
    )


def point(latitude: float, longitude: float) -> ColumnElement:
    """A bound-parameter point to compare against geography columns."""
    return cast(func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326), GeographyPoint())
