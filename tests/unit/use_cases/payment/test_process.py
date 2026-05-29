from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.domain.payment.enums import PaymentStatus
from src.domain.payment.exceptions import PaymentInvalidStateError
from src.usecases.payment.exceptions import PaymentNotFoundError
from src.usecases.payment.process import ProcessPaymentUseCase
from tests.unit.factories.payment import make_payment
from tests.unit.mocks.db.repositories.payment import MockPaymentRepository
from tests.unit.mocks.db.uow import MockUnitOfWork
from tests.unit.mocks.http.client import MockTransport
from tests.unit.mocks.payment_gateway.gateway import MockPaymentGateway


@pytest.mark.asyncio
async def test_process_payment_success_updates_status_to_succeeded(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    payment_gateway: MockPaymentGateway,
    http_client: AsyncClient,
) -> None:
    payment = make_payment()
    await payment_repo.create(payment)
    use_case = ProcessPaymentUseCase(uow, payment_repo, payment_gateway, http_client)

    await use_case.execute(payment.id)

    updated = await payment_repo.get_by_id(payment.id)
    assert updated.status == PaymentStatus.SUCCEEDED
    assert updated.processed_at is not None
    assert len(payment_gateway.charge_calls) == 1


@pytest.mark.asyncio
async def test_process_payment_declined_updates_status_to_failed(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    payment_gateway: MockPaymentGateway,
    http_client: AsyncClient,
) -> None:
    payment = make_payment()
    await payment_repo.create(payment)
    payment_gateway.set_decline("Insufficient funds")
    use_case = ProcessPaymentUseCase(uow, payment_repo, payment_gateway, http_client)

    await use_case.execute(payment.id)

    updated = await payment_repo.get_by_id(payment.id)
    assert updated.status == PaymentStatus.FAILED
    assert updated.failure_reason == "Insufficient funds"


@pytest.mark.asyncio
async def test_process_payment_sends_webhook(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    payment_gateway: MockPaymentGateway,
    http_client: AsyncClient,
    mock_transport: MockTransport,
) -> None:
    payment = make_payment(webhook_url="https://example.com/webhook")
    await payment_repo.create(payment)
    use_case = ProcessPaymentUseCase(uow, payment_repo, payment_gateway, http_client)

    await use_case.execute(payment.id)

    assert len(mock_transport.requests) == 1
    assert str(mock_transport.requests[0].url) == "https://example.com/webhook"


@pytest.mark.asyncio
async def test_process_payment_webhook_failure_does_not_raise(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    payment_gateway: MockPaymentGateway,
    http_client: AsyncClient,
    mock_transport: MockTransport,
) -> None:
    payment = make_payment()
    await payment_repo.create(payment)
    mock_transport.set_fail_next()
    use_case = ProcessPaymentUseCase(uow, payment_repo, payment_gateway, http_client)

    await use_case.execute(payment.id)

    updated = await payment_repo.get_by_id(payment.id)
    assert updated.status == PaymentStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_process_payment_not_found_raises_error(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    payment_gateway: MockPaymentGateway,
    http_client: AsyncClient,
) -> None:
    use_case = ProcessPaymentUseCase(uow, payment_repo, payment_gateway, http_client)

    with pytest.raises(PaymentNotFoundError):
        await use_case.execute(uuid4())


@pytest.mark.asyncio
async def test_process_already_processed_payment_raises_error(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    payment_gateway: MockPaymentGateway,
    http_client: AsyncClient,
) -> None:
    payment = make_payment(status=PaymentStatus.SUCCEEDED)
    await payment_repo.create(payment)
    use_case = ProcessPaymentUseCase(uow, payment_repo, payment_gateway, http_client)

    with pytest.raises(PaymentInvalidStateError):
        await use_case.execute(payment.id)

    assert payment_gateway.charge_calls == []


@pytest.mark.asyncio
async def test_process_payment_already_claimed_is_not_charged_again(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    payment_gateway: MockPaymentGateway,
    http_client: AsyncClient,
) -> None:
    payment = make_payment(status=PaymentStatus.PROCESSING)
    await payment_repo.create(payment)
    use_case = ProcessPaymentUseCase(uow, payment_repo, payment_gateway, http_client)

    with pytest.raises(PaymentInvalidStateError):
        await use_case.execute(payment.id)

    assert payment_gateway.charge_calls == []


@pytest.mark.asyncio
async def test_process_payment_uses_two_transactions(
    uow: MockUnitOfWork,
    payment_repo: MockPaymentRepository,
    payment_gateway: MockPaymentGateway,
    http_client: AsyncClient,
) -> None:
    payment = make_payment()
    await payment_repo.create(payment)
    use_case = ProcessPaymentUseCase(uow, payment_repo, payment_gateway, http_client)

    await use_case.execute(payment.id)

    assert uow.enter_calls == 2
    assert uow.exit_calls == 2
