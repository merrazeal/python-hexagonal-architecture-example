import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.payment.enums import Currency, PaymentStatus
from src.ports.db.repositories.exceptions import \
    PaymentNotFoundError as RepositoryPaymentNotFoundError
from src.ports.db.repositories.payment import IPaymentRepository
from src.usecases.payment.exceptions import PaymentNotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GetPaymentOutput:
    id: UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None
    failure_reason: str | None


class GetPaymentUseCase:
    def __init__(self, payment_repo: IPaymentRepository):
        self._payment_repo = payment_repo

    async def execute(self, payment_id: UUID) -> GetPaymentOutput:
        try:
            payment = await self._payment_repo.get_by_id(payment_id)
        except RepositoryPaymentNotFoundError as exc:
            raise PaymentNotFoundError(payment_id) from exc
        return GetPaymentOutput(
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
