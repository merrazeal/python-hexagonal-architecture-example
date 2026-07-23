import logging

from dishka import AsyncContainer

from src.ports.messaging.event_publisher import IEventPublisher
from src.ports.messaging.events.payment import DispatchPaymentsRequested
from src.rmq_config import PAYMENTS_DISPATCH_QUEUE_NAME

logger = logging.getLogger(__name__)


async def request_payment_dispatch(container: AsyncContainer) -> None:
    """Poller without logic: on every tick just publish a trigger event.

    The actual work (reading the outbox, publishing payment events) runs in
    the task manager (worker), which consumes this signal.
    """
    async with container() as scope:
        publisher = await scope.get(IEventPublisher)
        try:
            await publisher.publish(
                DispatchPaymentsRequested(),
                queue=PAYMENTS_DISPATCH_QUEUE_NAME,
            )
        except Exception:
            logger.exception("Failed to request payment dispatch")
