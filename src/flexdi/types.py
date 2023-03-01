from typing import Any, Callable, Coroutine, Protocol, Type, TypeVar, Union, overload

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
