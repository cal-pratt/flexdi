from abc import ABC, abstractmethod
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Iterator,
    Type,
    TypeVar,
    cast,
    overload,
)

T = TypeVar("T")


class ResolvableMixin(ABC):
    @overload
    async def resolve(self, func: Type[T]) -> T:
        # Handle class
        ...

    @overload
    async def resolve(self, func: Callable[..., AsyncIterator[T]]) -> T:
        # Handle async generators
        ...

    @overload
    async def resolve(self, func: Callable[..., Iterator[T]]) -> T:
        # Handle generators
        ...

    @overload
    async def resolve(self, func: Callable[..., Awaitable[T]]) -> T:
        # Handle async function
        ...

    @overload
    async def resolve(self, func: Callable[..., T]) -> T:
        # Handle function
        ...

    async def resolve(self, func: Callable[..., T]) -> T:
        """
        Resolve a callable using the graph.

        The callable provided may be a class, function, async function, generator,
        or async generator. The response object follows similar rules to the bindings,
        in that generators will be treated as context managers, pulling the value
        out which is yielded by the function.

        :param func: The callable to be resolved.
        :type func: Callable[..., T]

        :return: ``T``.
        """

        return cast(T, await self._resolve(func))

    @abstractmethod
    async def _resolve(self, func: Callable[..., Any]) -> Any:
        pass

    @abstractmethod
    async def resolve_args(
        self, func: Callable[..., Any], **extra: Any
    ) -> Dict[str, Any]:
        pass
