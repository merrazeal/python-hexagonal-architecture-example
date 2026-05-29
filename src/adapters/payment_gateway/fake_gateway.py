from decimal import Decimal
from uuid import UUID

from src.domain.payment.enums import Currency
from src.ports.payment_gateway.gateway import (IPaymentGateway,
                                               PaymentGatewayDeclinedError,
                                               PaymentGatewayUnavailableError)


class FakePaymentGateway(IPaymentGateway):
    def __init__(
        self,
        *,
        decline: bool = False,
        unavailable: bool = False,
    ) -> None:
        self._decline = decline
        self._unavailable = unavailable

    async def charge(
        self, amount: Decimal, currency: Currency, *, idempotency_key: UUID
    ) -> None:  # noqa: ARG002
        if self._unavailable:
            raise PaymentGatewayUnavailableError("Fake gateway unavailable")
        if self._decline:
            raise PaymentGatewayDeclinedError("Fake gateway declined")
