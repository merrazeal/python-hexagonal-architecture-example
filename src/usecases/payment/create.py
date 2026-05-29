import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.payment.entities import Payment
from src.domain.payment.enums import Currency, PaymentStatus
from src.ports.db.repositories.exceptions import DuplicateIdempotencyKeyError
from src.ports.db.repositories.payment import (IPaymentOutboxRepository,
                                               IPaymentRepository)
from src.ports.db.uow import IUnitOfWork
from src.usecases.payment.exceptions import PaymentAlreadyExistsError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreatePaymentInput:
    idempotency_key: str
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict
    webhook_url: str


@dataclass(frozen=True)
class CreatePaymentOutput:
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class CreatePaymentUseCase:
    def __init__(
        self,
        uow: IUnitOfWork,
        payment_repo: IPaymentRepository,
        outbox_repo: IPaymentOutboxRepository,
    ):
        self._uow = uow
        self._payment_repo = payment_repo
        self._outbox_repo = outbox_repo

    async def execute(self, command: CreatePaymentInput) -> CreatePaymentOutput:
        logger.debug(
            "Creating payment idempotency_key=%s amount=%s %s webhook_url=%s",
            command.idempotency_key,
            command.amount,
            command.currency,
            command.webhook_url,
        )

        existing = await self._payment_repo.get_by_idempotency_key(
            command.idempotency_key
        )
        if existing:
            logger.warning(
                "Duplicate payment request idempotency_key=%s", command.idempotency_key
            )
            raise PaymentAlreadyExistsError(command.idempotency_key)

        payment = Payment(
            id=uuid4(),
            amount=command.amount,
            currency=command.currency,
            description=command.description,
            metadata=command.metadata,
            status=PaymentStatus.PENDING,
            idempotency_key=command.idempotency_key,
            webhook_url=command.webhook_url,
            created_at=datetime.now(timezone.utc),
        )

        logger.debug(
            "Persisting payment payment_id=%s to repository and outbox", payment.id
        )
        try:
            async with self._uow:
                await self._payment_repo.create(payment)
                await self._outbox_repo.save(payment)
        except DuplicateIdempotencyKeyError:
            logger.warning(
                "Concurrent duplicate payment request idempotency_key=%s",
                command.idempotency_key,
            )
            raise PaymentAlreadyExistsError(command.idempotency_key)

        logger.info(
            "Payment created payment_id=%s amount=%s %s",
            payment.id,
            payment.amount,
            payment.currency,
        )
        return CreatePaymentOutput(
            payment_id=payment.id,
            status=payment.status,
            created_at=payment.created_at,
        )
