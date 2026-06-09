import asyncio

from app.core.database import session_factory
from app.messaging.broker import broker
from app.services.outbox import OutboxPublisher


async def main():
    await broker.connect()

    try:
        async with session_factory() as session:
            worker = OutboxPublisher(session)
            await worker.run_forever()
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
