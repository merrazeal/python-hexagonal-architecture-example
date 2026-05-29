from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from src.domain.payment.enums import Currency


class CreatePaymentRequest(BaseModel):
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict = Field(default_factory=dict)
    webhook_url: str

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("webhook_url")
    @classmethod
    def webhook_url_must_be_http(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("webhook_url must be a valid HTTP/HTTPS URL")
        return v
