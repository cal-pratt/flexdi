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
    """
    The ``FlexGraph`` is used to keep track of dependencies and invoke callables.

    When determining dependencies for a callable,  flexdi will examine the type
    annotations of the arguments, and populate the graph with dependencies which
    can satisfy the callable. A callable can be anything from a class (as seen
    with the type annotations), to functions, class methods, generators, etc.

    For complex types, flexdi allows binding helper functions that can map a type
    definition to an instance. These bindings can themselves be injected with
    dependencies. Bindings can also be defined as generators which allows supplying
    custom teardown logic for dependencies.

    When using the FlexGraph directly to resolve dependencies, it must be used as
    an asynchronous context manager. This ensures the proper teardown of any
    dependencies it creates during dependency resolution.

    .. code-block:: python

        graph = FlexGraph()

        @graph.bind()
        ...

        async with graph:
            result = graph.resolve(func)
    """

    def __init__(self) -> None:
        self._state = FlexState()

    @overload
    def bind(
        self,
        func: Func,
        *,
        resolves: Any = None,
        eager: bool = False,
    ) -> Func:
        ...

    @overload
    def bind(
        self,
        *,
        eager: bool = False,
        resolves: Any = None,
    ) -> Callable[[Func], Func]:
        ...

    def bind(
        self,
        func: Optional[Func] = None,
        *,
        resolves: Any = None,
        eager: bool = False,
    ) -> Union[Func, Callable[[Func], Func]]:
        """
        Bind a provider to a resolve a particular type.

        By default, this method will examine the return type annotations on the
        provided callable to determine what it should resolve. In cases where you
        want to be more specific, you can choose to explicitly list the value type
        that should be resolved.

        For generator and iterator type providers, the generic parameter will be
        pulled out and used to determine the type. i.e.

        * A function returning ``Iterator[T]`` binds to ``T``
        * A function returning ``Generator[T, U, V]`` binds to ``T``
        * A function returning ``AsyncIterator[T]`` binds to ``T``
        * A function returning ``AsyncGenerator[T, U]`` binds to ``T``

        If the binding is set as eager, the provider will be invoked as soon as
        the graph is opened. This is useful for applications which chain the
        graph instance.

        This method can be used as a no-argument decorator, a standard decorator,
        or used as a normal function call. e.g. these are all valid uses:

        .. code-block:: python

            @graph.bind
            def provide_foo() -> Foo:
                ...

            @graph.bind()
            def provide_foo() -> Foo:
                ...

            graph.bind(provide_foo)

        :param func: The callable that provides the binding, defaults to None
        :type func: Callable[..., T], optional

        :param resolves: The type or types that this provider binds to.
            defaults to the return type annotation of the provided func
        :type resolves: Any, optional

        :param eager: If the binding eager, defaults to False
        :type eager: bool

        :return: Either a decorator or the unedited function supplied.
        """

        def wrapper(_func: Func) -> Func:
            if self._state.opened:
                raise SetupError("FlexGraph opened. Cannot be bound.")

            self._state.add_binding(_func, resolves)
            self._state.add_policy(_func, eager=eager)
            return _func

        return wrapper(func) if func else wrapper

    def bind_instance(self, value: T, *, resolves: Any = None) -> T:
        """
        You can use this method to bind an already created instance of a class
        to the graph. By default, this method will examine the type of the provided
        instance to determine what it should type it should resolve to.

        .. code-block:: python

            graph = FlexGraph()
            graph.bind_instance(Configuration("my-config.json"))

        :param value: The instance for the binding.
        :type value: T

        :param resolves: The type or types that this provider binds to.
            defaults to ``type(value)``
        :type resolves: Any, optional

        :return: The unedited value supplied.
        """

        if self._state.opened:
            raise SetupError("FlexGraph opened. Cannot be bound.")

        self._state.add_binding(func := lambda: value, resolves or type(value))
        self._state.add_policy(func, eager=True)
        return value

    async def __aenter__(self) -> "FlexGraph":
        """
        Open the FlexGraph. See ``FlexGraph.open``
        """
        return await self.open()

    async def open(self) -> "FlexGraph":
        """
        When the FlexGraph is opened it will build a dependency tree given the
        provided bindings and create instances of any bindings which have been
        marked as eager.

        The FlexGraph uses an ``AsyncExitStack`` to keep track of context managers
        created during object initialization. Therefore, it must be opened prior
        to resolving any dependencies.

        :return: self
        """

        # Bind the current instance of the FlexGraph to any resolution.
        self.bind_instance(self, resolves=FlexGraph)
        await self._state.open()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        """
        Close the FlexGraph. See ``FlexGraph.open``
        """

        await self.close()

    async def close(self) -> None:
        """
        Close the FlexGraph and invoke the teardown of context managers invoked
        as part of dependency resolution.
        """

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

        if not self._state.opened:
            raise SetupError("Graph was not opened")
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
                async with self:
                    return await self.resolve(_self._func)

            def __call__(_self) -> T:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_self.aio())

        return _FuncEntrypoint(func) if func else _FuncEntrypoint

    def chain(self) -> "FlexGraph":
        """
        Graph chaining is the way that flexdi supports creating scopes for object
        resolution within applications. If a graph has been opened it is allowed
        to be chained.

        When a graph is chained, a child graph will be created which inherits a
        copy of the graph state found in the parent graph. Any objects created by
        the parent graph will persist in the child, but existing parent resources
        will not be closed or recreated until the parent exits. Any object created
        by the child graph instance will be destroyed when the child closes.
        """

        if not self._state.opened:
            raise SetupError("FlexGraph not opened. Cannot be chained.")

        graph = FlexGraph()
        graph._state = self._state.chain()
        return graph

    @contextmanager
    def override(self) -> Iterator["FlexGraph"]:
        """
        This context manager is primarily intended for testing use-cases.

        An override allow users to override dependency bindings with bindings in
        a way that temporary and will be reverted when the override is closed.

        The previous state of the graph is preserved by the context manager and
        is cloned into a temporary copy. When the context manager exits, the
        previous state is re-applied to the graph.

        :return: ``ContextManager[FlexGraph]``.
        """

        if self._state.opened:
            raise SetupError("FlexGraph already opened. Cannot be overriden.")

        state = self._state
        try:
            self._state = self._state.chain()
            yield self
        finally:
            self._state = state
