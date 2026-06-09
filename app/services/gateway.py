import asyncio
import random

from app.models.enums import PaymentStatus
from app.models.payment import Payment


class FakePaymentGateway:
    @staticmethod
    async def process(payment: Payment) -> PaymentStatus:
        await asyncio.sleep(random.randint(2, 5))

        if random.random() < 0.9:
            return PaymentStatus.SUCCEEDED

        return PaymentStatus.FAILED
