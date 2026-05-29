from uuid import UUID


class DuplicateIdempotencyKeyError(Exception):
    def __init__(self, idempotency_key: str):
        super().__init__(
            f"Payment with idempotency key '{idempotency_key}' already exists"
        )
        self.idempotency_key = idempotency_key


class PaymentNotFoundError(Exception):
    def __init__(self, payment_id: UUID):
        super().__init__(f"Payment {payment_id} not found")
        self.payment_id = payment_id
