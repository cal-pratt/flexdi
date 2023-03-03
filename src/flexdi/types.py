from abc import ABC, abstractmethod
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Coroutine,
    Iterator,
    Protocol,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

# Note, in 3.10+ we can start using TypeAlias
Clazz = Type[Any]
Func = Union[Clazz, Callable[..., Any]]
Instance = Any

T = TypeVar("T")
T_cov = TypeVar("T_cov", covariant=True)
FuncT = TypeVar("FuncT", bound=Callable[..., Any])
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


TOpen = TypeVar("TOpen", bound="Openable")


class Openable(ABC):
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


class Resolver(ABC):
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
    async def _resolve(self, func: Func) -> Instance:
        pass
