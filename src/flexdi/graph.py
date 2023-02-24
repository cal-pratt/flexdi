import asyncio
from contextlib import AsyncExitStack
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Coroutine,
    Iterator,
    Optional,
    Protocol,
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


class EntryPointDecorator(Protocol):
    @overload
    def __call__(self, func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[[], T]:
        ...

    @overload
    def __call__(self, func: Callable[..., T]) -> Callable[[], T]:
        ...

    def __call__(self, func: Any) -> Any:
        ...


class FlexGraph:
    def __init__(self) -> None:
        self._stack: Optional[AsyncExitStack] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._bindings = BindingMap()
        self._dependants = DependantMap()
        self._instances = InstanceMap()

    def chain(self) -> "FlexGraph":
        if not self._stack:
            raise SetupError("FlexGraph not opened. Cannot be chained.")

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
            raise SetupError(
                "FlexGraph already opened. Cannot add additional bindings."
            )

        def wrapper(_func: Func) -> Func:
            create_binding(
                target=resolves,
                func=_func,
                eager=eager,
                bindings=self._bindings,
                use_cached=False,
            )
            return _func

        return wrapper(func) if func else wrapper

    async def __aenter__(self) -> "FlexGraph":
        return await self.open()

    async def open(self) -> "FlexGraph":
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
                await self.close()
                raise
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.close()

    async def close(self) -> None:
        self._instances.clear()
        self._dependants.clear()
        if stack := self._stack:
            try:
                await stack.aclose()
            finally:
                self._stack = None

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
        if not (stack := self._stack):
            raise SetupError("FlexGraph not opened. Cannot be invoked.")

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

    @overload
    def entrypoint(
        self, func: Callable[..., Coroutine[Any, Any, T]]
    ) -> Callable[[], T]:
        ...

    @overload
    def entrypoint(self, func: Callable[..., T]) -> Callable[[], T]:
        ...

    @overload
    def entrypoint(self) -> EntryPointDecorator:
        ...

    def entrypoint(self, func: Any = None) -> Any:
        if self._stack:
            raise SetupError("FlexGraph already opened. Cannot add entrypoint.")

        def _wrapper(_func: Callable[..., T]) -> Callable[[], T]:
            async def _amain() -> T:
                async with self:
                    return await self.resolve(_func)

            def _main() -> T:
                if self._stack:
                    raise SetupError(
                        "FlexGraph already opened. Cannot run additional entrypoint."
                    )

                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    return loop.run_until_complete(_amain())
                else:
                    task = asyncio.run_coroutine_threadsafe(_amain(), loop)
                    return task.result()

            return _main

        return _wrapper(func) if func else _wrapper
