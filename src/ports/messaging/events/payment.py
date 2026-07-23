from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.domain.payment.enums import Currency


class PaymentCreatedEvent(BaseModel):
    payment_id: UUID
    amount: Decimal
    currency: Currency
    webhook_url: str


class DispatchPaymentsRequested(BaseModel):
    """Cron-tick signal: asks the task manager to dispatch pending payments.

    Carries no business data on purpose — the cron is a dumb poller, the
    decision of what to dispatch lives in the task handler / use case.
    """
