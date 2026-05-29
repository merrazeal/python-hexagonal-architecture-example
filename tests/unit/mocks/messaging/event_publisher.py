from typing import Any

from src.ports.messaging.event_publisher import IEventPublisher


class MockEventPublisher(IEventPublisher):
    def __init__(self) -> None:
        self.publish_calls: list[tuple[Any, str]] = []

    def reset_calls(self) -> None:
        self.publish_calls = []

    async def publish(self, event: Any, *, queue: str) -> None:
        self.publish_calls.append((event, queue))
