import logging
from uuid import UUID

from src.domain.payment.enums import PaymentStatus
from src.ports.db.repositories.payment import IPaymentOutboxRepository
from src.ports.db.uow import IUnitOfWork
from src.ports.messaging.event_publisher import IEventPublisher
from src.ports.messaging.events.payment import PaymentCreatedEvent

logger = logging.getLogger(__name__)


class DispatchPaymentEventsUseCase:
    def __init__(
        self,
        outbox_repo: IPaymentOutboxRepository,
        publisher: IEventPublisher,
        uow: IUnitOfWork,
        queue: str,
    ):
        self._outbox_repo = outbox_repo
        self._publisher = publisher
        self._uow = uow
        self._queue = queue

    async def execute(self, status: PaymentStatus) -> None:
        logger.debug("Fetching outbox messages status=%s", status)
        published_ids: list[UUID] = []

        async with self._uow:
            messages = await self._outbox_repo.get_by_status_for_update(status)

            if not messages:
                logger.debug("No outbox messages to dispatch status=%s", status)
                return

            logger.info(
                "Dispatching %d outbox messages status=%s topic=%s",
                len(messages),
                status,
                self._queue,
            )

            for msg in messages:
                logger.debug(
                    "Publishing event outbox_id=%s payment_id=%s",
                    msg.id,
                    msg.payment_id,
                )
                try:
                    await self._publisher.publish(
                        PaymentCreatedEvent(
                            payment_id=msg.payment_id,
                            amount=msg.amount,
                            currency=msg.currency,
                            webhook_url=msg.webhook_url,
                        ),
                        queue=self._queue,
                    )
                except Exception:
                    logger.exception(
                        "Failed to dispatch payment event outbox_id=%s payment_id=%s, skipping",
                        msg.id,
                        msg.payment_id,
                    )
                else:
                    logger.debug(
                        "Event published outbox_id=%s payment_id=%s",
                        msg.id,
                        msg.payment_id,
                    )
                    published_ids.append(msg.id)

            if published_ids:
                logger.debug("Marking %d events as published", len(published_ids))
                await self._outbox_repo.mark_published(published_ids)
