from pydantic import BaseModel
from uuid import UUID


class PaymentEvent(BaseModel):
    payment_id: UUID
    retry_count: int = 0