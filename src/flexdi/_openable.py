from abc import ABC, abstractmethod
from typing import Any, TypeVar

TOpen = TypeVar("TOpen", bound="OpenableMixin")


class OpenableMixin(ABC):
    opened: bool

    async def __aenter__(self: TOpen) -> TOpen:
        await self.open()
        return self

    @abstractmethod
    async def open(self) -> None:
        pass

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.close()

    @abstractmethod
    async def close(self) -> None:
        pass
