import logging

from dishka import AsyncContainer

from src.domain.payment.enums import PaymentStatus
from src.usecases.payment.dispatch import DispatchPaymentEventsUseCase

logger = logging.getLogger(__name__)


async def dispatch_payment_events(container: AsyncContainer) -> None:
    async with container() as scope:
        use_case = await scope.get(DispatchPaymentEventsUseCase)
        try:
            await use_case.execute(PaymentStatus.PENDING)
        except Exception:
            logger.exception("Failed to dispatch payment events")
