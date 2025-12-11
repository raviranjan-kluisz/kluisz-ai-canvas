from typing import TYPE_CHECKING, Optional, List
from uuid import UUID, uuid4

from sqlalchemy import Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from kluisz.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from kluisz.services.database.models.flow.model import Flow
    from kluisz.services.database.models.tenant.model import Tenant
    from kluisz.services.database.models.user.model import User

# Import FlowRead at runtime to resolve forward references
from kluisz.services.database.models.flow.model import FlowRead  # noqa: E402


class FolderBase(SQLModel):
    name: str = Field(index=True)
    description: str | None = Field(default=None, sa_column=Column(Text))
    auth_settings: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="Authentication settings for the folder/project",
    )


class Folder(FolderBase, table=True):  # type: ignore[call-arg]
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    parent_id: UUID | None = Field(default=None, foreign_key="folder.id")

    parent: Optional["Folder"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Folder.id"},
    )
    children: List["Folder"] = Relationship(
        sa_relationship=relationship("Folder", back_populates="parent")
    )
    user_id: UUID | None = Field(default=None, foreign_key="user.id")
    user: "User" = Relationship(back_populates="folders")
    tenant_id: UUIDstr | None = Field(
        default=None,
        foreign_key="tenant.id",
        index=True,
        nullable=True,
        description="Tenant this folder belongs to",
    )
    tenant: Optional["Tenant"] = Relationship(back_populates="folders")
    flows: List["Flow"] = Relationship(
        sa_relationship=relationship("Flow", back_populates="folder", cascade="all, delete, delete-orphan")
    )

    __table_args__ = (UniqueConstraint("user_id", "name", name="unique_folder_name"),)


class FolderCreate(FolderBase):
    components_list: List[UUID] | None = None
    flows_list: List[UUID] | None = None


class FolderRead(FolderBase):
    id: UUID
    parent_id: UUID | None = Field()


class FolderReadWithFlows(FolderBase):
    id: UUID
    parent_id: UUID | None = Field()
    flows: List[FlowRead] = Field(default=[])


class FolderUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    parent_id: UUID | None = None
    components: List[UUID] = Field(default_factory=list)
    flows: List[UUID] = Field(default_factory=list)
    auth_settings: dict | None = None


# Rebuild models to resolve forward references
FolderReadWithFlows.model_rebuild()
