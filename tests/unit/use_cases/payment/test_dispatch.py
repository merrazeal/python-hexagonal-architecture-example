from uuid import uuid4

import pytest

from src.domain.payment.enums import PaymentStatus
from src.ports.messaging.events.payment import PaymentCreatedEvent
from src.rmq_config import PAYMENTS_NEW_QUEUE
from src.usecases.payment.dispatch import DispatchPaymentEventsUseCase
from tests.unit.factories.payment import make_payment
from tests.unit.mocks.db.repositories.payment import \
    MockPaymentOutboxRepository
from tests.unit.mocks.db.uow import MockUnitOfWork
from tests.unit.mocks.messaging.event_publisher import MockEventPublisher


@pytest.mark.asyncio
async def test_dispatch_publishes_pending_messages(
    uow: MockUnitOfWork,
    outbox_repo: MockPaymentOutboxRepository,
    event_publisher: MockEventPublisher,
) -> None:
    payment = make_payment()
    await outbox_repo.save(payment)
    use_case = DispatchPaymentEventsUseCase(
        outbox_repo, event_publisher, uow, PAYMENTS_NEW_QUEUE
    )

    await use_case.execute(PaymentStatus.PENDING)

    assert len(event_publisher.publish_calls) == 1
    event, queue = event_publisher.publish_calls[0]
    assert isinstance(event, PaymentCreatedEvent)
    assert event.payment_id == payment.id
    assert queue == PAYMENTS_NEW_QUEUE


@pytest.mark.asyncio
async def test_dispatch_marks_messages_as_published(
    uow: MockUnitOfWork,
    outbox_repo: MockPaymentOutboxRepository,
    event_publisher: MockEventPublisher,
) -> None:
    payment = make_payment()
    await outbox_repo.save(payment)
    use_case = DispatchPaymentEventsUseCase(
        outbox_repo, event_publisher, uow, PAYMENTS_NEW_QUEUE
    )

    await use_case.execute(PaymentStatus.PENDING)

    unpublished = await outbox_repo.get_by_status_for_update(PaymentStatus.PENDING)
    assert unpublished == []


@pytest.mark.asyncio
async def test_dispatch_no_messages_does_nothing(
    uow: MockUnitOfWork,
    outbox_repo: MockPaymentOutboxRepository,
    event_publisher: MockEventPublisher,
) -> None:
    use_case = DispatchPaymentEventsUseCase(
        outbox_repo, event_publisher, uow, PAYMENTS_NEW_QUEUE
    )

    await use_case.execute(PaymentStatus.PENDING)

    assert event_publisher.publish_calls == []
    assert uow.enter_calls == 1
