from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        payment: Payment,
    ) -> Payment:
        self.session.add(payment)
        return payment

    async def get(self, payment_id):
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self,
        key: str,
    ) -> Payment | None:
        stmt = (
            select(Payment)
            .where(Payment.idempotency_key == key)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def update(self, payment):
        self.session.add(payment)
