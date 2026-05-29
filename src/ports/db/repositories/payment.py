import abc
from datetime import datetime
from uuid import UUID

from src.domain.payment.entities import Payment
from src.domain.payment.enums import PaymentStatus
from src.ports.db.repositories.output_dto import PaymentOutboxOutputDTO


class IPaymentRepository(abc.ABC):
    @abc.abstractmethod
    async def create(self, payment: Payment) -> Payment:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id(self, payment_id: UUID) -> Payment:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id_for_update(self, payment_id: UUID) -> Payment:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        processed_at: datetime | None,
        failure_reason: str | None = None,
    ) -> Payment:
        raise NotImplementedError


class IPaymentOutboxRepository(abc.ABC):
    @abc.abstractmethod
    async def save(self, payment: Payment) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_status_for_update(
        self, status: PaymentStatus
    ) -> list[PaymentOutboxOutputDTO]:
        raise NotImplementedError

    @abc.abstractmethod
    async def mark_published(self, outbox_ids: list[UUID]) -> None:
        raise NotImplementedError
