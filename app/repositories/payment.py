from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.enums import PaymentStatus


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payment: Payment) -> Payment:
        self.session.add(payment)
        return payment

    async def get(self, payment_id):
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(Payment.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def claim_for_processing(self, payment_id):
        stmt = (
            update(Payment)
            .where(
                Payment.id == payment_id,
                Payment.status == PaymentStatus.PENDING,
            )
            .values(
                status=PaymentStatus.PROCESSING,
            )
            .returning(Payment)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_succeeded(self, payment_id):
        await self.session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status=PaymentStatus.SUCCEEDED,
                processed_at=datetime.now(timezone.utc),
            )
        )

    async def mark_failed(self, payment_id):
        await self.session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status=PaymentStatus.FAILED,
                processed_at=datetime.now(timezone.utc),
            )
        )