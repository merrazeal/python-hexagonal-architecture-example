import dataclasses
from datetime import datetime, timezone
from decimal import Decimal
from typing import ClassVar
from uuid import UUID

from src.domain.payment.enums import Currency, PaymentStatus
from src.domain.payment.exceptions import InvalidPaymentTransitionError


@dataclasses.dataclass
class Payment:
    _ALLOWED_TRANSITIONS: ClassVar[dict[PaymentStatus, frozenset[PaymentStatus]]] = {
        PaymentStatus.PENDING: frozenset({PaymentStatus.PROCESSING}),
        PaymentStatus.PROCESSING: frozenset(
            {PaymentStatus.SUCCEEDED, PaymentStatus.FAILED}
        ),
    }
    id: UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("Payment amount must be positive")
        if not self.idempotency_key:
            raise ValueError("Idempotency key cannot be empty")
        if not self.webhook_url:
            raise ValueError("Webhook URL cannot be empty")

    def start_processing(self) -> "Payment":
        self._transition_to(PaymentStatus.PROCESSING)
        return dataclasses.replace(self, status=PaymentStatus.PROCESSING)

    def succeed(self) -> "Payment":
        self._transition_to(PaymentStatus.SUCCEEDED)
        return dataclasses.replace(
            self,
            status=PaymentStatus.SUCCEEDED,
            processed_at=datetime.now(timezone.utc),
        )

    def fail(self, reason: str) -> "Payment":
        if not reason:
            raise ValueError("Failure reason cannot be empty")
        self._transition_to(PaymentStatus.FAILED)
        return dataclasses.replace(
            self,
            status=PaymentStatus.FAILED,
            processed_at=datetime.now(timezone.utc),
            failure_reason=reason,
        )

    @property
    def is_pending(self) -> bool:
        return self.status == PaymentStatus.PENDING

    @property
    def is_processing(self) -> bool:
        return self.status == PaymentStatus.PROCESSING

    @property
    def is_terminal(self) -> bool:
        return self.status in (PaymentStatus.SUCCEEDED, PaymentStatus.FAILED)

    def _transition_to(self, new_status: PaymentStatus) -> None:
        allowed = self._ALLOWED_TRANSITIONS.get(self.status, frozenset())
        if new_status not in allowed:
            raise InvalidPaymentTransitionError(self.status, new_status)
