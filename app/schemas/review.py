from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Rating = Annotated[int, Field(ge=1, le=5)]
Comment = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)]


class ReviewCreate(BaseModel):
    rating: Rating
    comment: Comment | None = None

    @field_validator("comment")
    @classmethod
    def _blank_comment_is_none(cls, comment: str | None) -> str | None:
        return comment or None


class ReviewResponse(BaseModel):
    id: int
    order_id: int
    rating: int
    comment: str | None = None
    created_at: datetime
    # Shortened to first name and initial so public reviews don't expose full names.
    reviewer_name: str

    model_config = ConfigDict(from_attributes=True)
