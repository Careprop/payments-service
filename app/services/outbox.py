import asyncio

from app.messaging.broker import broker
from app.core.database import session_factory
from app.repositories.outbox import OutboxRepository


class OutboxPublisher:
    async def run_forever(self):
        while True:
            await self.run_once()
            await asyncio.sleep(1)

    async def run_once(self):
        async with session_factory() as session:
            repo = OutboxRepository(session)

            events = await repo.get_pending_for_update(limit=100)
            if not events:
                return

            claimed_events = await repo.mark_processing(
                [e.message_id for e in events]
            )
            await session.commit()

            results = await asyncio.gather(
                *(self.publish_event(e) for e in claimed_events),
                return_exceptions=True,
            )

            success_ids = [
                e.message_id
                for e, r in zip(claimed_events, results)
                if not isinstance(r, Exception)
            ]

            if success_ids:
                await repo.mark_processed(success_ids)
                await session.commit()

    @staticmethod
    async def publish_event(event):
        await broker.publish(
            {
                "payment_id": str(event.aggregate_id)
            },
            queue="payments.new",
        )
