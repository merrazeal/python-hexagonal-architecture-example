import logging
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.handlers.api.dependencies.auth import verify_api_key
from src.handlers.api.rest.v1.payment.input_schemas import CreatePaymentRequest
from src.handlers.api.rest.v1.payment.output_schemas import (
    CreatePaymentResponse, PaymentResponse)
from src.usecases.payment.create import (CreatePaymentInput,
                                         CreatePaymentUseCase)
from src.usecases.payment.exceptions import (PaymentAlreadyExistsError,
                                             PaymentNotFoundError)
from src.usecases.payment.get import GetPaymentUseCase

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/payments", tags=["payments"], dependencies=[Depends(verify_api_key)]
)


@router.post(
    "", status_code=status.HTTP_202_ACCEPTED, response_model=CreatePaymentResponse
)
@inject
async def create_payment(
    body: CreatePaymentRequest,
    use_case: FromDishka[CreatePaymentUseCase],
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> CreatePaymentResponse:
    try:
        payment = await use_case.execute(
            CreatePaymentInput(
                idempotency_key=idempotency_key,
                amount=body.amount,
                currency=body.currency,
                description=body.description,
                metadata=body.metadata,
                webhook_url=body.webhook_url,
            )
        )
    except PaymentAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment with this idempotency key already exists",
        )

    return CreatePaymentResponse(
        payment_id=payment.payment_id,
        status=payment.status,
        created_at=payment.created_at,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
@inject
async def get_payment(
    payment_id: UUID,
    use_case: FromDishka[GetPaymentUseCase],
) -> PaymentResponse:
    try:
        payment = await use_case.execute(payment_id)
    except PaymentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )

    return PaymentResponse(
        id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.metadata,
        status=payment.status,
        idempotency_key=payment.idempotency_key,
        webhook_url=payment.webhook_url,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
        failure_reason=payment.failure_reason,
    )
