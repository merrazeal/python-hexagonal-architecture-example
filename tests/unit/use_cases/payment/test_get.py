from uuid import uuid4

import pytest

from src.usecases.payment.exceptions import PaymentNotFoundError
from src.usecases.payment.get import GetPaymentUseCase
from tests.unit.factories.payment import make_payment
from tests.unit.mocks.db.repositories.payment import MockPaymentRepository


@pytest.mark.asyncio
async def test_get_payment_returns_payment_data(
    payment_repo: MockPaymentRepository,
) -> None:
    payment = make_payment()
    await payment_repo.create(payment)
    use_case = GetPaymentUseCase(payment_repo)

    result = await use_case.execute(payment.id)

    assert result.id == payment.id
    assert result.amount == payment.amount
    assert result.status == payment.status


@pytest.mark.asyncio
async def test_get_payment_not_found_raises_error(
    payment_repo: MockPaymentRepository,
) -> None:
    use_case = GetPaymentUseCase(payment_repo)

    with pytest.raises(PaymentNotFoundError):
        await use_case.execute(uuid4())
