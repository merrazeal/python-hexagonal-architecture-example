from src.domain.payment.enums import PaymentStatus


class InvalidPaymentTransitionError(Exception):
    def __init__(self, from_status: PaymentStatus, to_status: PaymentStatus):
        super().__init__(f"Cannot transition payment from {from_status} to {to_status}")
        self.from_status = from_status
        self.to_status = to_status


class PaymentInvalidStateError(Exception):
    def __init__(self, payment_id, status: PaymentStatus):
        super().__init__(
            f"Payment {payment_id} cannot be processed in state '{status}'"
        )
        self.payment_id = payment_id
        self.status = status
