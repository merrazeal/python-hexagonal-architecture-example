import asyncio
import uuid

import pytest
from httpx import AsyncClient

_POLL_INTERVAL = 1.0
_TIMEOUT = 30.0

_PAYMENT_PAYLOAD = {
    "amount": "100.00",
    "currency": "RUB",
    "description": "E2E test payment",
    "metadata": {"test": True},
    "webhook_url": "http://example.com/webhook",
}


async def _poll_until_status(
    client: AsyncClient,
    payment_id: str,
    headers: dict[str, str],
    expected_status: str,
) -> dict:
    deadline = asyncio.get_event_loop().time() + _TIMEOUT
    while asyncio.get_event_loop().time() < deadline:
        resp = await client.get(f"/api/v1/payments/{payment_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        if data["status"] == expected_status:
            return data
        await asyncio.sleep(_POLL_INTERVAL)
    raise TimeoutError(
        f"Payment {payment_id} did not reach '{expected_status}' within {_TIMEOUT}s"
    )


@pytest.mark.asyncio
async def test_payment_full_lifecycle(
    client_session: AsyncClient,
    api_headers: dict[str, str],
) -> None:
    create_resp = await client_session.post(
        "/api/v1/payments",
        json=_PAYMENT_PAYLOAD,
        headers={**api_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert create_resp.status_code == 202
    created = create_resp.json()
    assert created["status"] == "pending"
    payment_id = created["payment_id"]

    data = await _poll_until_status(
        client_session, payment_id, api_headers, "succeeded"
    )

    assert data["id"] == payment_id
    assert data["status"] == "succeeded"
    assert data["processed_at"] is not None
    assert data["failure_reason"] is None


@pytest.mark.asyncio
async def test_payment_idempotency(
    client_session: AsyncClient,
    api_headers: dict[str, str],
) -> None:
    idempotency_key = str(uuid.uuid4())
    headers = {**api_headers, "Idempotency-Key": idempotency_key}

    first = await client_session.post(
        "/api/v1/payments", json=_PAYMENT_PAYLOAD, headers=headers
    )
    assert first.status_code == 202

    second = await client_session.post(
        "/api/v1/payments", json=_PAYMENT_PAYLOAD, headers=headers
    )
    assert second.status_code == 409
