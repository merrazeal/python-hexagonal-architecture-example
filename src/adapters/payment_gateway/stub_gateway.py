import asyncio
import logging
import random
from decimal import Decimal
from uuid import UUID

from tenacity import (before_log, retry, retry_if_exception_type,
                      stop_after_attempt, wait_exponential)

from src.domain.payment.enums import Currency
from src.ports.payment_gateway.gateway import (IPaymentGateway,
                                               PaymentGatewayDeclinedError,
                                               PaymentGatewayUnavailableError)

_UNAVAILABLE_RATE = 0.05
_DECLINED_RATE = (
    _UNAVAILABLE_RATE + 0.10
)  # effective 10% declined after unavailable check
_MIN_DELAY = 2.0
_MAX_DELAY = 5.0

logger = logging.getLogger(__name__)


class StubPaymentGateway(IPaymentGateway):
    @retry(
        retry=retry_if_exception_type((PaymentGatewayUnavailableError,)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
        before=before_log(logger, logging.INFO),
    )
    async def charge(
        self, amount: Decimal, currency: Currency, *, idempotency_key: UUID
    ) -> None:  # noqa: ARG002
        await asyncio.sleep(random.uniform(_MIN_DELAY, _MAX_DELAY))

        roll = random.random()
        if roll < _UNAVAILABLE_RATE:
            raise PaymentGatewayUnavailableError("Mock gateway temporarily unavailable")
        if roll < _DECLINED_RATE:
            raise PaymentGatewayDeclinedError("Payment declined by issuing bank")
