from typing import Self

from src.ports.db.uow import IUnitOfWork


class MockUnitOfWork(IUnitOfWork):
    def __init__(self) -> None:
        self.commit_calls = 0
        self.rollback_calls = 0
        self.enter_calls = 0
        self.exit_calls = 0

    def reset_calls(self) -> None:
        self.commit_calls = 0
        self.rollback_calls = 0
        self.enter_calls = 0
        self.exit_calls = 0

    async def commit(self) -> None:
        self.commit_calls += 1

    async def rollback(self) -> None:
        self.rollback_calls += 1

    async def __aenter__(self) -> Self:
        self.enter_calls += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.exit_calls += 1
