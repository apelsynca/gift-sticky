from datetime import datetime
from typing import Annotated

from pydantic import UUID4, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Schema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, alias_generator=to_camel
    )


class IDSchema(Schema):
    id: Annotated[UUID4, Field(description="The ID of the object.")]


class TimestampedSchema(Schema):
    created_at: datetime = Field(description="Creation timestamp of the object.")
    updated_at: datetime | None = Field(
        description="Last update timestamp of the object."
    )
