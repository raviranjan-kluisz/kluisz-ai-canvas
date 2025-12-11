
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from kluisz.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from kluisz.services.database.models.tenant.model import Tenant


class File(SQLModel, table=True):  # type: ignore[call-arg]
    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    tenant_id: Optional[UUIDstr] = Field(
        default=None,
        foreign_key="tenant.id",
        nullable=True,
        description="Tenant this file belongs to",
        # Note: index is created by Alembic migration with proper naming convention
        # Don't use index=True here to avoid naming conflicts
    )
    tenant: Optional["Tenant"] = Relationship(back_populates="files")
    name: str = Field(nullable=False)
    path: str = Field(nullable=False)
    size: int = Field(nullable=False)
    provider: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("name", "user_id"),)
