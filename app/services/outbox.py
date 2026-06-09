import asyncio

from app.messaging.broker import broker
from app.repositories.outbox import OutboxRepository


class OutboxPublisher:
    def __init__(self, session):
        self.session = session
        self.repo = OutboxRepository(session)

    async def run_once(self):
        events = await self.repo.get_pending(limit=100)

        for event in events:
            await broker.publish(
                {
                    "message_id": str(event.message_id),
                    "payment_id": str(event.aggregate_id)
                },
                queue="payments.new"
            )
            await self.repo.mark_published(event=event)

        await self.session.commit()

    async def run_forever(self):
        while True:
            await self.run_once()
            await asyncio.sleep(1)