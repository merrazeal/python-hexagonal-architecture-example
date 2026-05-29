import dataclasses
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.payment.enums import Currency, PaymentStatus


@dataclasses.dataclass(frozen=True)
class PaymentOutboxOutputDTO:
    id: UUID
    payment_id: UUID
    status: PaymentStatus
    amount: Decimal
    currency: Currency
    webhook_url: str
    recorded_at: datetime
    published_at: datetime | None
