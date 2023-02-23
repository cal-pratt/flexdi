import asyncio
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
    Union,
    cast,
    overload,
)

from .binding import BindingMap, create_binding
from .dependant import DependantMap, create_dependant
from .errors import SetupError
from .instance import InstanceMap, create_instance

T = TypeVar("T")
Func = TypeVar("Func", bound=Callable[..., Any])


class FlexGraph:
    def __init__(self) -> None:
        self._stack: Optional[AsyncExitStack] = None
        self._bindings = BindingMap()
        self._dependants = DependantMap()
        self._instances = InstanceMap()

    def chain(self) -> "FlexGraph":
        if not self._stack:
            raise SetupError("FlexPack not opened. Cannot be chained.")

        flex = FlexGraph()
        flex._bindings = self._bindings.chain()
        flex._dependants = self._dependants.chain()
        flex._instances = self._instances.chain()
        return flex

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
        if self._stack:
            raise SetupError("FlexPack already opened. Cannot add additional bindings.")

        if func:
            create_binding(
                func=func,
                target=resolves,
                eager=eager,
                bindings=self._bindings,
                use_cached=False,
            )
            return func

        def wrapper(_func: Func) -> Func:
            create_binding(
                target=resolves,
                func=_func,
                eager=eager,
                bindings=self._bindings,
                use_cached=False,
            )
            return _func

        return wrapper

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
                for _, binding in list(self._bindings.items()):
                    create_dependant(
                        binding=binding,
                        bindings=self._bindings,
                        dependants=self._dependants,
                    )
                for _, binding in list(self._bindings.items()):
                    if binding.eager:
                        await create_instance(
                            dependant=self._dependants[binding.target],
                            instances=self._instances,
                            dependants=self._dependants,
                            stack=stack,
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
        self._instances.clear()
        self._dependants.clear()
        if stack := self._stack:
            try:
                await stack.aclose()
            finally:
                self._stack = None

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

        binding = create_binding(
            func=func,
            target=func,  # type: ignore
            bindings=self._bindings,
        )
        dependant = create_dependant(
            binding=binding,
            bindings=self._bindings,
            dependants=self._dependants,
        )
        instance = await create_instance(
            dependant=dependant,
            instances=self._instances,
            dependants=self._dependants,
            stack=stack,
        )
        return cast(T, instance)
