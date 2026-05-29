import pytest
from httpx import AsyncClient

from tests.unit.mocks.db.repositories.payment import (
    MockPaymentOutboxRepository, MockPaymentRepository)
from tests.unit.mocks.db.uow import MockUnitOfWork
from tests.unit.mocks.http.client import MockTransport
from tests.unit.mocks.messaging.event_publisher import MockEventPublisher
from tests.unit.mocks.payment_gateway.gateway import MockPaymentGateway


@pytest.fixture
def uow() -> MockUnitOfWork:
    return MockUnitOfWork()


@pytest.fixture
def payment_repo() -> MockPaymentRepository:
    return MockPaymentRepository()


@pytest.fixture
def outbox_repo() -> MockPaymentOutboxRepository:
    return MockPaymentOutboxRepository()


@pytest.fixture
def event_publisher() -> MockEventPublisher:
    return MockEventPublisher()


@pytest.fixture
def payment_gateway() -> MockPaymentGateway:
    return MockPaymentGateway()


@pytest.fixture
def mock_transport() -> MockTransport:
    return MockTransport()


@pytest.fixture
def http_client(mock_transport: MockTransport) -> AsyncClient:
    return AsyncClient(transport=mock_transport)
