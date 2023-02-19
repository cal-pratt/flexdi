import asyncio
import inspect
from contextlib import AsyncExitStack
from types import TracebackType
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Coroutine,
    Iterator,
    Optional,
    Type,
    TypeVar,
    cast,
    overload,
)

from .dependant import Dependant, DependantCache, create_dependant
from .invoker import CallCache, call_dependant

T = TypeVar("T")
Func = TypeVar("Func", bound=Callable[..., Any])


class Injector:
    def __init__(self) -> None:
        self._singleton_deps: list[Dependant] = []
        self._deps_cache = DependantCache()
        self._call_cache = CallCache()
        self._stack: Optional[AsyncExitStack] = None

    def binding(
        self, *, scope: str = "request", bind_to: Any = None
    ) -> Callable[[Func], Func]:
        assert scope in ("request", "singleton")

        def wrapper(func: Func) -> Func:
            nonlocal bind_to
            if bind_to is None:
                signature = inspect.signature(func)
                bind_to = signature.return_annotation

            dep = create_dependant(bind_to, func, cache=self._deps_cache, override=True)
            if scope == "singleton":
                self._singleton_deps.append(dep)
            return func

        return wrapper

    def __enter__(self) -> "Injector":
        return self

    async def __aenter__(self) -> "Injector":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        return asyncio.run(self.__aexit__(exc_type, exc, traceback))

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        self._call_cache = CallCache()
        if stack := self._stack:
            try:
                async with stack:
                    pass
            finally:
                self._stack = None
        return None

    @overload
    def invoke(self, func: Type[T]) -> T:
        # Handle class
        ...

    @overload
    def invoke(self, func: Callable[..., AsyncIterator[T]]) -> T:
        # Handle async generators
        ...

    @overload
    def invoke(self, func: Callable[..., Iterator[T]]) -> T:
        # Handle generators
        ...

    @overload
    def invoke(self, func: Callable[..., Coroutine[Any, Any, T]]) -> T:
        # Handle async function
        ...

    @overload
    def invoke(self, func: Callable[..., T]) -> T:
        # Handle function
        ...

    def invoke(self, func: Callable[..., T]) -> T:
        return asyncio.run(self.ainvoke(func))

    @overload
    async def ainvoke(self, func: Type[T]) -> T:
        # Handle class
        ...

    @overload
    async def ainvoke(self, func: Callable[..., AsyncIterator[T]]) -> T:
        # Handle async generators
        ...

    @overload
    async def ainvoke(self, func: Callable[..., Iterator[T]]) -> T:
        # Handle generators
        ...

    @overload
    async def ainvoke(self, func: Callable[..., Coroutine[Any, Any, T]]) -> T:
        # Handle async function
        ...

    @overload
    async def ainvoke(self, func: Callable[..., T]) -> T:
        # Handle function
        ...

    async def ainvoke(self, func: Callable[..., T]) -> T:
        deps_cache = self._deps_cache.chain()
        call_cache = self._call_cache.chain()
        stack = await self._init_stack()

        if isinstance(func, type):
            clazz = func
        else:
            # create a unique class to represent the function we're invoking, to be unique
            # and avoid any potential caching of the objects return value.
            class Sentinel:
                pass

            clazz = Sentinel

        dep = create_dependant(clazz, func, cache=deps_cache, store=False)
        res = await call_dependant(dep, cache=call_cache, stack=stack, store=False)

        return cast(T, res)

    async def _init_stack(self) -> AsyncExitStack:
        if not (stack := self._stack):
            stack = AsyncExitStack()
            for dep in self._singleton_deps:
                if dep.key not in self._call_cache:
                    await call_dependant(
                        dep,
                        cache=self._call_cache,
                        stack=stack,
                        override=True,
                    )
            self._stack = stack
        return stack
