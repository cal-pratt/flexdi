import asyncio
from contextlib import AsyncExitStack
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Coroutine,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from .dependant import Dependant, DependantCache, create_dependant
from .errors import SetupError
from .invoker import CallCache, call_dependant
from .util import provider_return_type

T = TypeVar("T")
Func = TypeVar("Func", bound=Callable[..., Any])


class FlexGraph:
    def __init__(self) -> None:
        self._eager_deps: List[Dependant] = []
        self._deps_cache = DependantCache()
        self._call_cache = CallCache()
        self._stack: Optional[AsyncExitStack] = None

    @overload
    def bind(self, func: Func, *, eager: bool = False, target: Any = None) -> Func:
        ...

    @overload
    def bind(
        self, *, eager: bool = False, target: Any = None
    ) -> Callable[[Func], Func]:
        ...

    def bind(
        self, func: Optional[Func] = None, *, eager: bool = False, target: Any = None
    ) -> Union[Func, Callable[[Func], Func]]:
        if func:
            self._bind(func, eager=eager, target=target)
            return func

        def wrapper(_func: Func) -> Func:
            self._bind(_func, eager=eager, target=target)
            return _func

        return wrapper

    def _bind(self, func: Any, *, eager: bool = False, target: Any) -> None:
        if self._stack:
            raise SetupError("FlexPack already opened. Cannot add additional bindings.")

        if target is None:
            target = provider_return_type(func)

        dep = create_dependant(target, func, cache=self._deps_cache, override=True)
        if eager:
            self._eager_deps.append(dep)

    def __enter__(self) -> "FlexGraph":
        return self.open()

    async def __aenter__(self) -> "FlexGraph":
        return await self.aopen()

    def open(self) -> "FlexGraph":
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.aopen())

    async def aopen(self) -> "FlexGraph":
        if not self._stack:
            self._stack = stack = AsyncExitStack()
            try:
                for dep in self._eager_deps:
                    if dep.key not in self._call_cache:
                        await call_dependant(
                            dep,
                            cache=self._call_cache,
                            stack=stack,
                            override=True,
                        )
            except:  # noqa: E722
                await self.aclose()
                raise
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        self.close()

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.aclose()

    def close(self) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.aclose())

    async def aclose(self) -> None:
        self._call_cache = CallCache()
        if stack := self._stack:
            try:
                await stack.aclose()
            finally:
                self._stack = None

    def chain(self) -> "FlexGraph":
        if not self._stack:
            raise SetupError("FlexPack not opened. Cannot be chained.")

        flex = FlexGraph()
        flex._call_cache = self._call_cache.chain()
        flex._deps_cache = self._deps_cache.chain()
        return flex

    @overload
    def resolve(self, func: Type[T]) -> T:
        # Handle class
        ...

    @overload
    def resolve(self, func: Callable[..., AsyncIterator[T]]) -> T:
        # Handle async generators
        ...

    @overload
    def resolve(self, func: Callable[..., Iterator[T]]) -> T:
        # Handle generators
        ...

    @overload
    def resolve(self, func: Callable[..., Coroutine[Any, Any, T]]) -> T:
        # Handle async function
        ...

    @overload
    def resolve(self, func: Callable[..., T]) -> T:
        # Handle function
        ...

    def resolve(self, func: Callable[..., T]) -> T:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.aresolve(func))

    @overload
    async def aresolve(self, func: Type[T]) -> T:
        # Handle class
        ...

    @overload
    async def aresolve(self, func: Callable[..., AsyncIterator[T]]) -> T:
        # Handle async generators
        ...

    @overload
    async def aresolve(self, func: Callable[..., Iterator[T]]) -> T:
        # Handle generators
        ...

    @overload
    async def aresolve(self, func: Callable[..., Coroutine[Any, Any, T]]) -> T:
        # Handle async function
        ...

    @overload
    async def aresolve(self, func: Callable[..., T]) -> T:
        # Handle function
        ...

    async def aresolve(self, func: Callable[..., T]) -> T:
        if not (stack := self._stack):
            raise SetupError("FlexPack not opened. Cannot be invoked.")

        dep = create_dependant(func, func, cache=self._deps_cache)
        res = await call_dependant(dep, cache=self._call_cache, stack=stack)
        return cast(T, res)
