from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import status

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import validate_api_key
from app.schemas.payment import CreatePaymentRequest
from app.schemas.payment import CreatePaymentResponse
from app.schemas.payment import PaymentResponse
from app.services.payment import PaymentService


router = APIRouter(
    prefix="/api/v1/payments",
    tags=["payments"],
)


@router.post(
    "",
    response_model=CreatePaymentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(validate_api_key)],
)
async def create_payment(
    payload: CreatePaymentRequest,
    session: AsyncSession = Depends(get_session),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
    ),
):
    service = PaymentService(session)

    payment = await service.create_payment(
        payload,
        idempotency_key,
    )

    return CreatePaymentResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    dependencies=[Depends(validate_api_key)],
)
async def get_payment(
    payment_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    service = PaymentService(session)

    payment = await service.get_payment(
        payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment
