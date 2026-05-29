import abc
from decimal import Decimal
from uuid import UUID

from src.domain.payment.enums import Currency


class PaymentGatewayUnavailableError(Exception):
    """Raised when the payment gateway is unreachable or returns an unexpected error."""


class PaymentGatewayDeclinedError(Exception):
    """Raised when the gateway successfully processed the request but declined the payment."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class IPaymentGateway(abc.ABC):
    @abc.abstractmethod
    async def charge(
        self, amount: Decimal, currency: Currency, *, idempotency_key: UUID
    ) -> None:
        raise NotImplementedError
