import logging
import random

import httpx
from tenacity import (before_log, retry, retry_if_exception_type,
                      stop_after_attempt, wait_exponential)

logger = logging.getLogger(__name__)

_NETWORK_ERROR_RATE = 0.05
_ERROR_RESPONSE_RATE = _NETWORK_ERROR_RATE + 0.10


class StubHttpTransport(httpx.AsyncBaseTransport):
    @retry(
        retry=retry_if_exception_type((httpx.ConnectError,)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
        before=before_log(logger, logging.INFO),
    )
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        roll = random.random()
        if roll < _NETWORK_ERROR_RATE:
            raise httpx.ConnectError("Stub network error", request=request)
        if roll < _ERROR_RESPONSE_RATE:
            logger.info("Stub HTTP %s %s -> 500", request.method, request.url)
            return httpx.Response(500)
        logger.info("Stub HTTP %s %s -> 200", request.method, request.url)
        return httpx.Response(200)
