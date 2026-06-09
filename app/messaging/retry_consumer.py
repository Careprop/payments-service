import asyncio

from app.messaging.broker import broker
from app.messaging.schemas import PaymentEvent

from app.core.database import session_factory
from app.repositories.payment import PaymentRepository
from app.services.webhook import WebhookService


MAX_RETRIES = 3

webhook = WebhookService()


@broker.subscriber("payments.retry")
async def retry_handler(event: PaymentEvent):
    async with session_factory() as session:
        repo = PaymentRepository(session)
        payment = await repo.get(event.payment_id)
        if not payment:
            return

        try:
            delay = 2 ** event.retry_count
            await asyncio.sleep(delay)

            await webhook.send(
                payment.webhook_url,
                {
                    "payment_id": str(payment.id),
                    "status": payment.status.value
                }
            )

        except Exception:

            next_retry = event.retry_count + 1
            if next_retry >= MAX_RETRIES:
                await broker.publish(
                    {
                        "payment_id": str(payment.id),
                        "retry_count": next_retry,
                    },
                    queue="payments.dlq",
                )

                return

            await broker.publish(
                {
                    "payment_id": str(payment.id),
                    "retry_count": next_retry,
                },
                queue="payments.retry",
            )
