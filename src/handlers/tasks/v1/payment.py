from dishka.integrations.faststream import FromDishka, inject
from faststream import Logger
from faststream.rabbit import RabbitRoute

from src.domain.payment.exceptions import PaymentInvalidStateError
from src.ports.messaging.events.payment import PaymentCreatedEvent
from src.rmq_config import (PAYMENTS_DEAD_QUEUE, PAYMENTS_DLX,
                            PAYMENTS_EXCHANGE, PAYMENTS_QUEUE)
from src.usecases.payment.exceptions import PaymentNotFoundError
from src.usecases.payment.process import ProcessPaymentUseCase


@inject
async def handle_payment_created(
    event: PaymentCreatedEvent,
    logger: Logger,
    use_case: FromDishka[ProcessPaymentUseCase],
) -> None:
    logger.info("Received payment.created event for payment_id=%s", event.payment_id)
    try:
        await use_case.execute(event.payment_id)
    except PaymentNotFoundError:
        logger.warning("Payment %s not found, dropping message", event.payment_id)
    except PaymentInvalidStateError as exc:
        logger.warning(
            "Payment %s already processed (status=%s), dropping duplicate message",
            event.payment_id,
            exc.status,
        )


@inject
async def handle_payment_dead_letter(
    event: PaymentCreatedEvent, logger: Logger
) -> None:
    logger.error("Payment %s landed in DLQ after exhausted retries", event.payment_id)


v1_payment_handlers = [
    RabbitRoute(handle_payment_created, PAYMENTS_QUEUE, exchange=PAYMENTS_EXCHANGE),
    RabbitRoute(handle_payment_dead_letter, PAYMENTS_DEAD_QUEUE, exchange=PAYMENTS_DLX),
]
