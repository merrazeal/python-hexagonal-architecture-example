import logging
from uuid import UUID

from httpx import AsyncClient

from src.domain.payment.exceptions import PaymentInvalidStateError
from src.ports.db.repositories.exceptions import \
    PaymentNotFoundError as RepositoryPaymentNotFoundError
from src.ports.db.repositories.payment import IPaymentRepository
from src.ports.db.uow import IUnitOfWork
from src.ports.payment_gateway.gateway import (IPaymentGateway,
                                               PaymentGatewayDeclinedError)
from src.usecases.payment.exceptions import PaymentNotFoundError

logger = logging.getLogger(__name__)


class ProcessPaymentUseCase:
    def __init__(
        self,
        uow: IUnitOfWork,
        payment_repo: IPaymentRepository,
        gateway: IPaymentGateway,
        http_client: AsyncClient,  # meh, stable enough, not worth abstracting!
    ):
        self._uow = uow
        self._payment_repo = payment_repo
        self._gateway = gateway
        self._http_client = http_client

    async def execute(self, payment_id: UUID) -> None:
        # Phase 1: lock the row, validate the state and claim the payment by moving it to PROCESSING.
        async with self._uow:
            try:
                payment = await self._payment_repo.get_by_id_for_update(payment_id)
            except RepositoryPaymentNotFoundError as exc:
                raise PaymentNotFoundError(payment_id) from exc

            if not payment.is_pending:
                raise PaymentInvalidStateError(payment_id, payment.status)

            processing = payment.start_processing()
            await self._payment_repo.update_status(
                payment_id=processing.id,
                status=processing.status,
                processed_at=None,
                failure_reason=None,
            )
        logger.info(
            "Payment claimed for processing payment_id=%s amount=%s %s",
            payment_id,
            processing.amount,
            processing.currency,
        )

        # Phase 2: call the external gateway
        try:
            logger.debug(
                "Charging gateway payment_id=%s idempotency_key=%s",
                payment_id,
                processing.id,
            )
            await self._gateway.charge(
                processing.amount, processing.currency, idempotency_key=processing.id
            )
            logger.info("Gateway charge succeeded payment_id=%s", payment_id)
            updated = processing.succeed()
        except PaymentGatewayDeclinedError as exc:
            logger.warning(
                "Gateway declined payment payment_id=%s reason=%s",
                payment_id,
                exc.reason,
            )
            updated = processing.fail(exc.reason)

        # Phase 3: persist the terminal state in a second short transaction.
        async with self._uow:
            await self._payment_repo.update_status(
                payment_id=updated.id,
                status=updated.status,
                processed_at=updated.processed_at,
                failure_reason=updated.failure_reason,
            )
        logger.info(
            "Payment status updated payment_id=%s status=%s", payment_id, updated.status
        )

        logger.debug(
            "Delivering webhook payment_id=%s url=%s", payment_id, updated.webhook_url
        )
        try:
            await self._http_client.post(
                updated.webhook_url,
                json={"payment_id": str(updated.id), "status": updated.status.value},
            )
            logger.info(
                "Webhook delivered payment_id=%s url=%s",
                payment_id,
                updated.webhook_url,
            )
        except Exception:
            logger.exception(
                "Webhook delivery failed payment_id=%s url=%s",
                payment_id,
                updated.webhook_url,
            )
