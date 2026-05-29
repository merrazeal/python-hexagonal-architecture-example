from typing import Any

from faststream.rabbit import RabbitBroker

from src.ports.messaging.event_publisher import IEventPublisher


class RabbitmqPublisher(IEventPublisher):
    def __init__(self, broker: RabbitBroker):
        self._broker = broker

    async def publish(self, event: Any, *, queue: str) -> None:
        await self._broker.publish(event, queue=queue)
