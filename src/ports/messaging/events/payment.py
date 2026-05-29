from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.domain.payment.enums import Currency


class PaymentCreatedEvent(BaseModel):
    payment_id: UUID
    amount: Decimal
    currency: Currency
    webhook_url: str
