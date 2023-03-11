import asyncio
from typing import Any, Callable, Coroutine, Generic, Protocol, TypeVar, overload

from flexdi._resolvable import ResolvableMixin

T = TypeVar("T")
T_cov = TypeVar("T_cov", covariant=True)
AsyncEntry = Callable[..., Coroutine[Any, Any, T]]
Entry = Callable[..., T]


class Entrypoint(Protocol[T_cov]):
    def __call__(self) -> T_cov:
        raise NotImplementedError

    async def aio(self) -> T_cov:
        raise NotImplementedError


class EntrypointDecorator(Protocol):
    @overload
    def __call__(self, func: AsyncEntry[T]) -> Entrypoint[T]:
        ...

    @overload
    def __call__(self, func: Entry[T]) -> Entrypoint[T]:
        ...

    def __call__(self, func: Any) -> Any:
        ...


class EntrypointMixin(ResolvableMixin):
    @overload
    def entrypoint(self, func: AsyncEntry[T]) -> Entrypoint[T]:
        ...

    @overload
    def entrypoint(self, func: Entry[T]) -> Entrypoint[T]:
        ...

    @overload
    def entrypoint(self) -> EntrypointDecorator:
        ...

    def entrypoint(self, func: Any = None) -> Any:
        """
        A helper tool to construct an async function which will open the graph
        and invoke a callable, and a no-argument synchronous method which will
        invoke the async function.

        :param func: The callable to be wrapped.
        :type func: Callable[..., T]

        :return: ``Callable[[], T]``.
        """

        class _FuncEntrypoint(Generic[T]):
            def __init__(_self, _func: Callable[..., T]) -> None:
                _self._func = _func

            async def aio(_self) -> T:
                return await self.resolve(_self._func)

            def __call__(_self) -> T:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self.resolve(_self._func))

        return _FuncEntrypoint(func) if func else _FuncEntrypoint
