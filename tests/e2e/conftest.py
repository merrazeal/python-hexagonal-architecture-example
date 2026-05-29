from typing import AsyncIterator

import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.e2e.settings import E2ESettings

_settings = E2ESettings()


@pytest_asyncio.fixture
async def client_session() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(base_url=_settings.base_url) as client:
        yield client


@pytest.fixture(scope="session")
def base_url() -> str:
    return _settings.base_url


@pytest.fixture(scope="session")
def api_headers() -> dict[str, str]:
    return {"X-API-Key": _settings.api_key}
