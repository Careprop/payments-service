import asyncio

from app.messaging.broker import broker
from app.services.outbox import OutboxPublisher


async def main():
    await broker.connect()

    publisher = OutboxPublisher()

    await publisher.run_forever()


if __name__ == "__main__":
    asyncio.run(main())