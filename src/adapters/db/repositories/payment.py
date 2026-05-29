from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.db.tables.payment import payment_outbox_table, payment_table
from src.domain.payment.entities import Payment
from src.domain.payment.enums import Currency, PaymentStatus
from src.ports.db.repositories.exceptions import DuplicateIdempotencyKeyError
from src.ports.db.repositories.exceptions import \
    PaymentNotFoundError as RepositoryPaymentNotFoundError
from src.ports.db.repositories.output_dto import PaymentOutboxOutputDTO
from src.ports.db.repositories.payment import (IPaymentOutboxRepository,
                                               IPaymentRepository)


class PaymentRepository(IPaymentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, payment: Payment) -> Payment:
        try:
            await self._session.execute(
                insert(payment_table).values(
                    id=payment.id,
                    amount=payment.amount,
                    currency=payment.currency.value,
                    description=payment.description,
                    metadata=payment.metadata,
                    status=payment.status.value,
                    idempotency_key=payment.idempotency_key,
                    webhook_url=payment.webhook_url,
                    created_at=payment.created_at,
                    processed_at=payment.processed_at,
                    failure_reason=payment.failure_reason,
                )
            )
        except IntegrityError:
            raise DuplicateIdempotencyKeyError(payment.idempotency_key)
        return payment

    async def get_by_id(self, payment_id: UUID) -> Payment:
        result = await self._session.execute(
            select(payment_table).where(payment_table.c.id == payment_id)
        )
        row = result.fetchone()
        if row is None:
            raise RepositoryPaymentNotFoundError(payment_id)
        return self._from_row(row)

    async def get_by_id_for_update(self, payment_id: UUID) -> Payment:
        result = await self._session.execute(
            select(payment_table)
            .where(payment_table.c.id == payment_id)
            .with_for_update()
        )
        row = result.fetchone()
        if row is None:
            raise RepositoryPaymentNotFoundError(payment_id)
        return self._from_row(row)

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        result = await self._session.execute(
            select(payment_table).where(payment_table.c.idempotency_key == key)
        )
        row = result.fetchone()
        return self._from_row(row) if row else None

    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        processed_at: datetime | None,
        failure_reason: str | None = None,
    ) -> Payment:
        await self._session.execute(
            update(payment_table)
            .where(payment_table.c.id == payment_id)
            .values(
                status=status.value,
                processed_at=processed_at,
                failure_reason=failure_reason,
            )
        )
        return await self.get_by_id(payment_id)

    @staticmethod
    def _from_row(row) -> Payment:
        return Payment(
            id=row.id,
            amount=row.amount,
            currency=Currency(row.currency),
            description=row.description,
            metadata=row.metadata,
            status=PaymentStatus(row.status),
            idempotency_key=row.idempotency_key,
            webhook_url=row.webhook_url,
            created_at=row.created_at,
            processed_at=row.processed_at,
            failure_reason=row.failure_reason,
        )


class PaymentOutboxRepository(IPaymentOutboxRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, payment: Payment) -> None:
        await self._session.execute(
            insert(payment_outbox_table).values(
                id=uuid4(),
                payment_id=payment.id,
                status=payment.status.value,
                amount=payment.amount,
                currency=payment.currency.value,
                webhook_url=payment.webhook_url,
                recorded_at=datetime.now(timezone.utc),
                published_at=None,
            )
        )

    async def get_by_status_for_update(
        self, status: PaymentStatus
    ) -> list[PaymentOutboxOutputDTO]:
        result = await self._session.execute(
            select(payment_outbox_table)
            .where(
                payment_outbox_table.c.status == status.value,
                payment_outbox_table.c.published_at.is_(None),
            )
            .order_by(payment_outbox_table.c.recorded_at)
            .with_for_update(skip_locked=True)
        )
        return [self._to_dto(row) for row in result.fetchall()]

    async def mark_published(self, outbox_ids: list[UUID]) -> None:
        await self._session.execute(
            update(payment_outbox_table)
            .where(payment_outbox_table.c.id.in_(outbox_ids))
            .values(published_at=datetime.now(timezone.utc))
        )

    @staticmethod
    def _to_dto(row) -> PaymentOutboxOutputDTO:
        return PaymentOutboxOutputDTO(
            id=row.id,
            payment_id=row.payment_id,
            status=PaymentStatus(row.status),
            amount=row.amount,
            currency=Currency(row.currency),
            webhook_url=row.webhook_url,
            recorded_at=row.recorded_at,
            published_at=row.published_at,
        )
