from app.messaging.broker import broker
from app.messaging.schemas import PaymentEvent


@broker.subscriber("payments.dlq")
async def dead_letter_handler(event: PaymentEvent):
    print(f"Message moved to DLQ. payment_id={event.payment_id} retry_count={event.retry_count}")
    return
