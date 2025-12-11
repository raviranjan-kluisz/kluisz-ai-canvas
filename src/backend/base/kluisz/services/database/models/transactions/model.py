from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import field_serializer, field_validator
from sqlmodel import JSON, Column, Field, SQLModel

from kluisz.schema.serialize import UUIDstr
from kluisz.serialization.serialization import get_max_items_length, get_max_text_length, serialize


class TransactionBase(SQLModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    vertex_id: str | None = Field(default=None, nullable=True)
    target_id: str | None = Field(default=None)
    inputs: dict | None = Field(default=None, sa_column=Column(JSON))
    outputs: dict | None = Field(default=None, sa_column=Column(JSON))
    status: str | None = Field(default=None, nullable=True)
    error: str | None = Field(default=None)
    flow_id: UUID | None = Field(default=None, nullable=True, foreign_key="flow.id", index=True)
    
    # Credit Transaction Fields (for credit transactions)
    user_id: UUIDstr | None = Field(
        default=None,
        nullable=True,
        foreign_key="user.id",
        index=True,
        description="User for credit transactions",
    )
    transaction_type: str | None = Field(
        default=None,
        nullable=True,
        index=True,
        description="Transaction type: deduction, addition, refund, purchase, upgrade, downgrade",
    )
    credits_amount: int | None = Field(
        default=None,
        nullable=True,
        ge=0,
        description="Credits amount for this transaction",
    )
    credits_before: int | None = Field(
        default=None,
        nullable=True,
        ge=0,
        description="Credits balance before transaction",
    )
    credits_after: int | None = Field(
        default=None,
        nullable=True,
        ge=0,
        description="Credits balance after transaction",
    )
    usage_record_id: str | None = Field(
        default=None,
        nullable=True,
        description="Link to usage record (e.g., Langfuse trace ID)",
    )
    transaction_metadata: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional transaction metadata",
    )
    created_by: UUIDstr | None = Field(
        default=None,
        nullable=True,
        foreign_key="user.id",
        description="User who created this transaction",
    )

    # Needed for Column(JSON)
    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        # Filter out the 'code' key from inputs before creating the model
        if "inputs" in data and isinstance(data["inputs"], dict) and "code" in data["inputs"]:
            # IMPORTANT: Copy the inputs dict before mutation to avoid modifying the original
            # dictionary that was passed in. Without this copy, we would mutate the caller's data.
            inputs_copy = data["inputs"].copy()
            inputs_copy.pop("code")
            data["inputs"] = inputs_copy
        super().__init__(**data)

    @field_validator("flow_id", mode="before")
    @classmethod
    def validate_flow_id(cls, value):
        if value is None:
            return value
        if isinstance(value, str):
            value = UUID(value)
        return value

    @field_serializer("inputs")
    def serialize_inputs(self, data) -> dict:
        """Serialize the transaction's input data with enforced limits on text length and item count.

        Parameters:
            data (dict): The input data to be serialized.

        Returns:
            dict: The serialized input data with applied constraints.
        """
        # Filter out the "code" key from inputs if present
        if isinstance(data, dict) and "code" in data:
            # IMPORTANT: Copy the data dict before mutation to avoid modifying the original
            # dictionary. Without this copy, we would mutate the field's actual data.
            data_copy = data.copy()
            data_copy.pop("code")
            data = data_copy

        return serialize(data, max_length=get_max_text_length(), max_items=get_max_items_length())

    @field_serializer("outputs")
    def serialize_outputs(self, data) -> dict:
        """Serialize the outputs dictionary with enforced limits on text length and item count.

        Parameters:
            data (dict): The outputs data to serialize.

        Returns:
            dict: The serialized outputs dictionary with applied constraints.
        """
        return serialize(data, max_length=get_max_text_length(), max_items=get_max_items_length())


class TransactionTable(TransactionBase, table=True):  # type: ignore[call-arg]
    __tablename__ = "transaction"
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)


class TransactionReadResponse(TransactionBase):
    id: UUID = Field(alias="transaction_id")
    flow_id: UUID
