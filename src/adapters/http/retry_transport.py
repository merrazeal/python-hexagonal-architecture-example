import logging

import httpx
from tenacity import (before_log, retry, retry_if_exception_type,
                      stop_after_attempt, wait_exponential)

logger = logging.getLogger(__name__)


class RetryTransport(httpx.AsyncBaseTransport):
    def __init__(self, transport: httpx.AsyncBaseTransport) -> None:
        self._transport = transport

    @retry(
        retry=retry_if_exception_type(
            (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)
        ),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
        before=before_log(logger, logging.INFO),
    )
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return await self._transport.handle_async_request(request)
