from pydantic import BaseModel, Field


class Pagination(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)
    page: int = Field(default=1, ge=1)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit
