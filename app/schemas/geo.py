"""Validated geographic coordinates (WGS 84 degrees). NaN and infinity are rejected."""

from typing import Annotated

from pydantic import BaseModel, Field

Latitude = Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
Longitude = Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]


class Coordinates(BaseModel):
    latitude: Latitude
    longitude: Longitude
