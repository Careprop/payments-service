from enum import StrEnum


class Currency(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = 'processing'
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = 'processing'
    PUBLISHED = "published"
    FAILED = "failed"  # unused
