import asyncio
from contextlib import contextmanager
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Coroutine,
    Generic,
    Iterator,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from .errors import SetupError
from .state import FlexState

T = TypeVar("T")
T_cov = TypeVar("T_cov", covariant=True)
Func = TypeVar("Func", bound=Callable[..., Any])
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


class FlexGraph:
    def __init__(self) -> None:
        self._state = FlexState()

    @overload
    def bind(self, func: Func, *, eager: bool = False, resolves: Any = None) -> Func:
        ...

    @overload
    def bind(
        self, *, eager: bool = False, resolves: Any = None
    ) -> Callable[[Func], Func]:
        ...

    def bind(
        self, func: Optional[Func] = None, *, eager: bool = False, resolves: Any = None
    ) -> Union[Func, Callable[[Func], Func]]:
        def wrapper(_func: Func) -> Func:
            if self._state.opened:
                raise SetupError("FlexGraph opened. Cannot be bound.")

            self._state.binding(_func, target=resolves, eager=eager, use_cached=False)
            return _func

        return wrapper(func) if func else wrapper

    def bind_instance(self, value: T, *, resolves: Any = None) -> T:
        resolves = resolves or type(value)
        self._state.binding(
            lambda: value, target=resolves, eager=True, use_cached=False
        )
        return value

    async def __aenter__(self) -> "FlexGraph":
        return await self.open()

    async def open(self) -> "FlexGraph":
        await self._state.open()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._state.close()

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
        if not self._state.opened:
            raise SetupError("FlexGraph not opened. Cannot be resolved.")

        return cast(T, await self._state.resolve(func))

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
        class _FuncEntrypoint(Generic[T]):
            def __init__(_self, _func: Callable[..., T]) -> None:
                _self._func = _func

            async def aio(_self) -> T:
                if self._state.opened:
                    return await self.resolve(_self._func)
                else:
                    async with self:
                        return await self.resolve(_self._func)

            def __call__(_self) -> T:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_self.aio())

        return _FuncEntrypoint(func) if func else _FuncEntrypoint

    def chain(self) -> "FlexGraph":
        if not self._state.opened:
            raise SetupError("FlexGraph not opened. Cannot be chained.")

        graph = FlexGraph()
        graph._state = self._state.chain()
        return graph

    @contextmanager
    def override(self) -> Iterator["FlexGraph"]:
        if self._state.opened:
            raise SetupError("FlexGraph already opened. Cannot be overriden.")

        state = self._state
        try:
            self._state = self._state.chain()
            yield self
        finally:
            self._state = state
