from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OutboxStatus
from app.models.outbox import Outbox


LEASE_TIMEOUT = timedelta(minutes=2)


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        event: Outbox,
    ) -> Outbox:
        self.session.add(event)
        return event

    async def get_pending_for_update(
            self,
            limit: int = 100,
    ) -> list[Outbox]:
        stmt = (
            select(Outbox)
            .where(
                or_(
                    Outbox.status == OutboxStatus.PENDING,
                    (
                        (Outbox.status == OutboxStatus.PROCESSING)
                        & (
                            Outbox.processing_started_at
                            < datetime.now(timezone.utc) - LEASE_TIMEOUT
                        )
                    ),
                )
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def mark_processing(self, event_ids: list) -> list[Outbox]:
        if not event_ids:
            return []

        stmt = (
            update(Outbox)
            .where(
                Outbox.message_id.in_(event_ids),
            )
            .values(
                status=OutboxStatus.PROCESSING,
                processing_started_at=datetime.now(timezone.utc),
            )
            .returning(Outbox)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_processed(
            self,
            event_ids: list,
    ) -> None:
        if not event_ids:
            return

        await self.session.execute(
            update(Outbox)
            .where(Outbox.message_id.in_(event_ids))
            .values(
                status=OutboxStatus.PUBLISHED,
                processing_started_at=None,
                published_at=datetime.now(timezone.utc)
            )
        )

    async def mark_failed(self, message_id):
        await self.session.execute(
            update(Outbox)
            .where(Outbox.message_id == message_id)
            .values(
                status=OutboxStatus.FAILED,
            )
        )