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

        payment = await repo.claim_for_processing(event.payment_id)
        if not payment:
            return

        await session.commit()

        result = await gateway.process(payment=payment)
        if result == PaymentStatus.SUCCEEDED:
            await repo.mark_succeeded(payment.id)
        else:
            await repo.mark_failed(payment.id)

        await session.commit()

        try:
            await webhook.send(
                payment.webhook_url,
                {
                    "payment_id": str(payment.id),
                    "status": PaymentStatus.SUCCEEDED.value,
                },
            )

        except Exception:
            await broker.publish(
                {
                    "payment_id": str(payment.id),
                    "retry_count": 0,
                },
                queue="payments.retry",
            )
