from datetime import datetime, timezone

from sqlalchemy import select

from app.models.enums import OutboxStatus
from app.models.outbox import Outbox


class OutboxRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, event: Outbox) -> Outbox:
        self.session.add(event)
        return event

    async def get_pending(self, limit: int = 100):
        stmt = (
            select(Outbox)
            .where(Outbox.status == OutboxStatus.PENDING)
            .order_by(Outbox.created_at.asc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_published(self, event: Outbox) -> None:
        event.status = OutboxStatus.PUBLISHED
        event.published_at = datetime.utcnow()

        self.session.add(event)
