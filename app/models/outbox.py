import uuid
from datetime import datetime

from sqlalchemy import JSON
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base
from app.models.base import TimestampMixin
from app.models.enums import OutboxStatus


class Outbox(Base, TimestampMixin):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4,
        unique=True,
    )

    aggregate_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus),
        default=OutboxStatus.PENDING,
        nullable=False,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
