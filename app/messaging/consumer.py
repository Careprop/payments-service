from app.messaging.broker import broker
from app.messaging.schemas import PaymentEvent

from app.services.gateway import FakePaymentGateway
from app.services.webhook import WebhookService
from app.models.enums import PaymentStatus
from app.repositories.payment import PaymentRepository
from app.core.database import session_factory


gateway = FakePaymentGateway()
webhook = WebhookService()


@broker.subscriber("payments.new")
async def process_payment(event: PaymentEvent):
    async with session_factory() as session:
        repo = PaymentRepository(session)

        payment = await repo.get(event.payment_id)
        if not payment:
            return

        if payment.status != PaymentStatus.PENDING:
            return

        result = await gateway.process(payment=payment)
        payment.status = result

        await repo.update(payment)
        await session.commit()

        try:
            await webhook.send(
                payment.webhook_url,
                {
                    "payment_id": str(payment.id),
                    "status": payment.status.value
                }
            )
        except Exception:
            await broker.publish(
                {
                    "payment_id": str(payment.id),
                    "retry_count": 0
                },
                queue="payments.retry"
            )
