import dataclasses
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.domain.payment.entities import Payment
from src.domain.payment.enums import PaymentStatus
from src.ports.db.repositories.exceptions import (DuplicateIdempotencyKeyError,
                                                  PaymentNotFoundError)
from src.ports.db.repositories.output_dto import PaymentOutboxOutputDTO
from src.ports.db.repositories.payment import (IPaymentOutboxRepository,
                                               IPaymentRepository)


class MockPaymentRepository(IPaymentRepository):
    def __init__(self) -> None:
        self._by_id: dict[UUID, Payment] = {}
        self._by_idempotency_key: dict[str, UUID] = {}

    async def create(self, payment: Payment) -> Payment:
        if payment.idempotency_key in self._by_idempotency_key:
            raise DuplicateIdempotencyKeyError(payment.idempotency_key)
        self._by_id[payment.id] = payment
        self._by_idempotency_key[payment.idempotency_key] = payment.id
        return payment

    async def get_by_id(self, payment_id: UUID) -> Payment:
        payment = self._by_id.get(payment_id)
        if payment is None:
            raise PaymentNotFoundError(payment_id)
        return payment

    async def get_by_id_for_update(self, payment_id: UUID) -> Payment:
        return await self.get_by_id(payment_id)

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        payment_id = self._by_idempotency_key.get(key)
        if payment_id is None:
            return None
        return self._by_id.get(payment_id)

    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        processed_at: datetime | None,
        failure_reason: str | None = None,
    ) -> Payment:
        payment = await self.get_by_id(payment_id)
        updated = dataclasses.replace(
            payment,
            status=status,
            failure_reason=failure_reason,
            processed_at=processed_at,
        )
        self._by_id[payment_id] = updated
        return updated


class MockPaymentOutboxRepository(IPaymentOutboxRepository):
    def __init__(self) -> None:
        self._records: list[PaymentOutboxOutputDTO] = []

    async def save(self, payment: Payment) -> None:
        self._records.append(
            PaymentOutboxOutputDTO(
                id=uuid4(),
                payment_id=payment.id,
                status=payment.status,
                amount=payment.amount,
                currency=payment.currency,
                webhook_url=payment.webhook_url,
                recorded_at=datetime.now(timezone.utc),
                published_at=None,
            )
        )

    async def get_by_status_for_update(
        self, status: PaymentStatus
    ) -> list[PaymentOutboxOutputDTO]:
        return [
            r for r in self._records if r.status == status and r.published_at is None
        ]

    async def mark_published(self, outbox_ids: list[UUID]) -> None:
        ids = set(outbox_ids)
        now = datetime.now(timezone.utc)
        self._records = [
            dataclasses.replace(r, published_at=now) if r.id in ids else r
            for r in self._records
        ]
