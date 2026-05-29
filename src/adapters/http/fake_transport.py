import httpx


class FakeHttpTransport(httpx.AsyncBaseTransport):
    def __init__(self, *, status_code: int = 200) -> None:
        self._status_code = status_code

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(self._status_code)
