import asyncio
import inspect
from contextlib import AsyncExitStack
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

        if self._stack:
            raise Exception("Context already opened.")

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
        return asyncio.run(self._enter())

    def __exit__(self, *args: Any, **kwargs: Any) -> Optional[bool]:
        return asyncio.run(self._exit())

    async def __aenter__(self) -> "Injector":
        return await self._enter()

    async def __aexit__(self, *args: Any, **kwargs: Any) -> Optional[bool]:
        await self._exit()
        return None

    async def _enter(self) -> "Injector":
        if not self._stack:
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
        return self

    async def _exit(self) -> None:
        self._call_cache = CallCache()
        if stack := self._stack:
            try:
                async with stack:
                    pass
            finally:
                self._stack = None

    def chain(self) -> "Injector":
        if not self._stack:
            raise Exception("Context was not opened for injector")

        injector = Injector()
        injector._call_cache = self._call_cache.chain()
        injector._deps_cache = self._deps_cache.chain()
        return injector

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
        if not (stack := self._stack):
            raise Exception("Context was not opened for injector")

        dep = create_dependant(func, func, cache=self._deps_cache)
        res = await call_dependant(dep, cache=self._call_cache, stack=stack)
        return cast(T, res)
