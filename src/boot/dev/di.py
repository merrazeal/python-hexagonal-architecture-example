import logging
from typing import AsyncIterator

from dishka import (AsyncContainer, Provider, Scope, make_async_container,
                    provide)
from faststream.rabbit import RabbitBroker
from httpx import AsyncClient, AsyncHTTPTransport, Timeout
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)

from src.adapters.db.repositories.payment import (PaymentOutboxRepository,
                                                  PaymentRepository)
from src.adapters.db.uow import SqlAlchemyUnitOfWork
from src.adapters.http.stub_transport import StubHttpTransport
from src.adapters.messaging.rabbitmq_publisher import RabbitmqPublisher
from src.adapters.payment_gateway.stub_gateway import StubPaymentGateway
from src.config import settings
from src.ports.db.repositories.payment import (IPaymentOutboxRepository,
                                               IPaymentRepository)
from src.ports.db.uow import IUnitOfWork
from src.ports.messaging.event_publisher import IEventPublisher
from src.ports.payment_gateway.gateway import IPaymentGateway
from src.rmq_config import PAYMENTS_NEW_QUEUE
from src.usecases.payment.create import CreatePaymentUseCase
from src.usecases.payment.dispatch import DispatchPaymentEventsUseCase
from src.usecases.payment.get import GetPaymentUseCase
from src.usecases.payment.process import ProcessPaymentUseCase

logger = logging.getLogger(__name__)


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_engine(self) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(
            settings.database_url,
            pool_size=10,
            max_overflow=15,
            pool_pre_ping=True,
            connect_args={
                "server_settings": {"idle_in_transaction_session_timeout": "30000"}
            },
        )
        try:
            yield engine
        finally:
            await engine.dispose()

    @provide(scope=Scope.APP)
    def get_session_maker(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_maker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session


class MessageBrokerProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_broker(self) -> AsyncIterator[RabbitBroker]:
        broker = RabbitBroker(settings.rabbitmq_url)
        await broker.connect()
        try:
            yield broker
        finally:
            await broker.stop()

    @provide(scope=Scope.APP)
    def get_event_publisher(self, broker: RabbitBroker) -> IEventPublisher:
        return RabbitmqPublisher(broker)


class RepositoryProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_payment_repo(self, session: AsyncSession) -> IPaymentRepository:
        return PaymentRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_payment_outbox_repo(
        self, session: AsyncSession
    ) -> IPaymentOutboxRepository:
        return PaymentOutboxRepository(session)


class UnitOfWorkProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_uow(self, session: AsyncSession) -> IUnitOfWork:
        return SqlAlchemyUnitOfWork(session)


class HttpProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_http_client(self) -> AsyncIterator[AsyncClient]:
        client = AsyncClient(
            transport=StubHttpTransport(),
            timeout=Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0),
        )
        try:
            yield client
        finally:
            await client.aclose()


class GatewayProvider(Provider):
    @provide(scope=Scope.APP)
    def get_payment_gateway(self) -> IPaymentGateway:
        return StubPaymentGateway()


class UseCaseProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_create_payment(
        self,
        uow: IUnitOfWork,
        payment_repo: IPaymentRepository,
        outbox_repo: IPaymentOutboxRepository,
    ) -> CreatePaymentUseCase:
        return CreatePaymentUseCase(uow, payment_repo, outbox_repo)

    @provide(scope=Scope.REQUEST)
    def get_get_payment(self, payment_repo: IPaymentRepository) -> GetPaymentUseCase:
        return GetPaymentUseCase(payment_repo)

    @provide(scope=Scope.REQUEST)
    def get_process_payment(
        self,
        uow: IUnitOfWork,
        payment_repo: IPaymentRepository,
        gateway: IPaymentGateway,
        http_client: AsyncClient,
    ) -> ProcessPaymentUseCase:
        return ProcessPaymentUseCase(uow, payment_repo, gateway, http_client)

    @provide(scope=Scope.REQUEST)
    def get_dispatch_payment_events(
        self,
        outbox_repo: IPaymentOutboxRepository,
        publisher: IEventPublisher,
        uow: IUnitOfWork,
    ) -> DispatchPaymentEventsUseCase:
        return DispatchPaymentEventsUseCase(
            outbox_repo, publisher, uow, PAYMENTS_NEW_QUEUE
        )


def get_container() -> AsyncContainer:
    return make_async_container(
        DatabaseProvider(),
        MessageBrokerProvider(),
        HttpProvider(),
        RepositoryProvider(),
        UnitOfWorkProvider(),
        GatewayProvider(),
        UseCaseProvider(),
    )
