import abc
from typing import Any


class IEventPublisher(abc.ABC):
    @abc.abstractmethod
    async def publish(self, event: Any, *, queue: str) -> None:
        raise NotImplementedError
