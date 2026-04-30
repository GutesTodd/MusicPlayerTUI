from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class BaseEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Any = Field(description="Уникальный инденфикатор сущности")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))


class BaseValueObject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class BaseCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_id: UUID = Field(default_factory=uuid4)


class BaseEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    timestamp: float = Field(default_factory=datetime.now(UTC).timestamp)
