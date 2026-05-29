from decimal import Decimal

import pytest

from src.domain.payment.enums import Currency, PaymentStatus
from src.usecases.payment.create import (CreatePaymentInput,
                                         CreatePaymentUseCase)
from src.usecases.payment.exceptions import PaymentAlreadyExistsError
from tests.unit.mocks.db.repositories.payment import (
    MockPaymentOutboxRepository, MockPaymentRepository)
from tests.unit.mocks.db.uow import MockUnitOfWork

_COMMAND = CreatePaymentInput(
    idempotency_key="idem-key-1",
    amount=Decimal("100.00"),
    currency=Currency.RUB,
    description="Order #1",
    metadata={"order_id": 1},
    webhook_url="https://example.com/webhook",
)


@pytest.mark.asyncio
async def test_create_payment_returns_pending_status(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    outbox_repo: MockPaymentOutboxRepository,
) -> None:
    use_case = CreatePaymentUseCase(uow, payment_repo, outbox_repo)

    result = await use_case.execute(_COMMAND)

    assert result.status == PaymentStatus.PENDING
    assert result.payment_id is not None
    assert result.created_at is not None


@pytest.mark.asyncio
async def test_create_payment_persists_to_repo_and_outbox(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    outbox_repo: MockPaymentOutboxRepository,
) -> None:
    use_case = CreatePaymentUseCase(uow, payment_repo, outbox_repo)

    result = await use_case.execute(_COMMAND)

    saved = await payment_repo.get_by_id(result.payment_id)
    assert saved.amount == _COMMAND.amount
    assert saved.currency == _COMMAND.currency
    assert len(outbox_repo._records) == 1
    assert outbox_repo._records[0].payment_id == result.payment_id


@pytest.mark.asyncio
async def test_create_payment_wraps_in_uow(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    outbox_repo: MockPaymentOutboxRepository,
) -> None:
    use_case = CreatePaymentUseCase(uow, payment_repo, outbox_repo)

    await use_case.execute(_COMMAND)

    assert uow.enter_calls == 1
    assert uow.exit_calls == 1


@pytest.mark.asyncio
async def test_create_payment_duplicate_idempotency_key_raises_error(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    outbox_repo: MockPaymentOutboxRepository,
) -> None:
    use_case = CreatePaymentUseCase(uow, payment_repo, outbox_repo)
    await use_case.execute(_COMMAND)

    with pytest.raises(PaymentAlreadyExistsError) as exc_info:
        await use_case.execute(_COMMAND)

    assert exc_info.value.idempotency_key == _COMMAND.idempotency_key
