from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.models.enums import Currency
from app.models.enums import PaymentStatus


class CreatePaymentRequest(BaseModel):
    amount: Decimal
    currency: Currency
    description: str | None = None
    extra_data: dict = {}
    webhook_url: HttpUrl


class CreatePaymentResponse(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: Decimal
    currency: Currency
    description: str | None
    extra_data: dict
    status: PaymentStatus
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None
