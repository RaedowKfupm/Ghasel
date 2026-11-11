from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.fields import Phone, ShortText
from app.schemas.geo import Latitude, Longitude
from app.schemas.pagination import Pagination

ServiceRadiusKm = Annotated[float, Field(gt=0, le=100, allow_inf_nan=False)]


class _PairedCoordinates(BaseModel):
    """Latitude and longitude are either both supplied or both omitted."""

    latitude: Latitude | None = None
    longitude: Longitude | None = None

    @model_validator(mode="after")
    def _coordinates_are_paired(self) -> Self:
        supplied = {"latitude", "longitude"} & self.model_fields_set
        if len(supplied) == 1 or (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class BranchCreate(_PairedCoordinates):
    branch_name: ShortText
    branch_address: ShortText
    phone: Phone
    service_radius_km: ServiceRadiusKm = 10


class BranchUpdate(_PairedCoordinates):
    branch_name: ShortText | None = None
    branch_address: ShortText | None = None
    phone: Phone | None = None
    service_radius_km: ServiceRadiusKm | None = None


class BranchResponse(BaseModel):
    id: int
    laundry_id: int
    laundry_name: str
    branch_name: str | None = None
    branch_address: str
    phone: str
    latitude: float | None = None
    longitude: float | None = None
    service_radius_km: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RatedBranchResponse(BranchResponse):
    """A branch with its rating aggregated from real customer reviews."""

    rating_average: float | None = None  # None until the branch has a review
    rating_count: int


class NearbyBranchResponse(RatedBranchResponse):
    distance_km: float


class NearbySearch(Pagination):
    latitude: Latitude
    longitude: Longitude
    radius_km: Annotated[float, Field(gt=0, le=50, allow_inf_nan=False)] = 5
