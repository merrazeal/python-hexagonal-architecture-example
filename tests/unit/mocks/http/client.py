import httpx


class MockTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self._fail_next: bool = False

    def set_fail_next(self) -> None:
        self._fail_next = True

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self._fail_next:
            self._fail_next = False
            raise httpx.ConnectError("Mock network error", request=request)
        return httpx.Response(200)
