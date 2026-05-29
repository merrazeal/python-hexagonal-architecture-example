from decimal import Decimal
from uuid import UUID

from src.domain.payment.enums import Currency
from src.ports.payment_gateway.gateway import (IPaymentGateway,
                                               PaymentGatewayDeclinedError)


class MockPaymentGateway(IPaymentGateway):
    def __init__(self) -> None:
        self.charge_calls: list[tuple[Decimal, Currency, UUID]] = []
        self._decline_reason: str | None = None

    def set_decline(self, reason: str) -> None:
        self._decline_reason = reason

    def reset_calls(self) -> None:
        self.charge_calls = []
        self._decline_reason = None

    async def charge(
        self, amount: Decimal, currency: Currency, *, idempotency_key: UUID
    ) -> None:
        self.charge_calls.append((amount, currency, idempotency_key))
        if self._decline_reason is not None:
            raise PaymentGatewayDeclinedError(self._decline_reason)
