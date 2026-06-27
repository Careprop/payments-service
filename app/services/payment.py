import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import Outbox
from app.models.payment import Payment
from app.models.enums import OutboxStatus, PaymentStatus
from app.repositories.outbox import OutboxRepository
from app.repositories.payment import PaymentRepository
from app.schemas.payment import CreatePaymentRequest


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.payment_repo = PaymentRepository(session)
        self.outbox_repo = OutboxRepository(session)

    async def create_payment(
            self,
            payload: CreatePaymentRequest,
            idempotency_key: str,
    ) -> Payment:

        payment = Payment(
            id=uuid.uuid4(),
            amount=payload.amount,
            currency=payload.currency,
            description=payload.description,
            extra_data=payload.extra_data,
            webhook_url=str(payload.webhook_url),
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
        )

        outbox_event = Outbox(
            aggregate_id=payment.id,
            event_type="payment_created",
            payload={"payment_id": str(payment.id)},
            status=OutboxStatus.PENDING,
        )

        try:
            await self.payment_repo.create(payment)
            await self.outbox_repo.create(outbox_event)
            await self.session.commit()
            return payment

        except IntegrityError:
            await self.session.rollback()
            existing = await self.payment_repo.get_by_idempotency_key(idempotency_key)
            if existing is None:
                raise
            return existing

    async def get_payment(self, payment_id: uuid.UUID) -> Payment | None:
        return await self.payment_repo.get(payment_id)
