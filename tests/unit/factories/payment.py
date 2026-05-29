from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from src.domain.payment.entities import Payment
from src.domain.payment.enums import Currency, PaymentStatus


def make_payment(**kwargs) -> Payment:
    defaults = dict(
        id=uuid4(),
        amount=Decimal("100.00"),
        currency=Currency.RUB,
        description="Test",
        metadata={},
        status=PaymentStatus.PENDING,
        idempotency_key="key-1",
        webhook_url="https://example.com/webhook",
        created_at=datetime.now(timezone.utc),
    )
    return Payment(**{**defaults, **kwargs})
