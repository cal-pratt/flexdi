import asyncio
from contextlib import contextmanager
from typing import Any, Callable, Generic, Iterator, Optional, Union, overload

from .errors import SetupError
from .rules import FlexRules
from .scope import GraphScope
from .types import (
    AsyncEntry,
    Entry,
    Entrypoint,
    EntrypointDecorator,
    FuncT,
    ScopeName,
    T,
)


class FlexGraph(GraphScope):
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

    When using the FlexGraph directly to resolve dependencies, it creates scopes
    which ensures the proper caching, startup and teardown of any dependencies
    it creates during dependency resolution.

    .. code-block:: python

        graph = FlexGraph()

        @graph.bind()
        def my_provider(...) -> ...:
            ...

        result = await graph.resolve(func)
    """

    def __init__(self) -> None:
        super().__init__(FlexRules())

    @overload
    def bind(
        self,
        func: FuncT,
        *,
        scope: ScopeName = "request",
        resolves: Any = None,
        eager: bool = False,
    ) -> FuncT:
        ...

    @overload
    def bind(
        self,
        *,
        scope: ScopeName = "request",
        eager: bool = False,
        resolves: Any = None,
    ) -> Callable[[FuncT], FuncT]:
        ...

    def bind(
        self,
        func: Optional[FuncT] = None,
        *,
        scope: ScopeName = "request",
        resolves: Any = None,
        eager: bool = False,
    ) -> Union[FuncT, Callable[[FuncT], FuncT]]:
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

        :param scope: The scope for the dependency. Defaults to "request".
        :type scope: "application" | "request"

        :param resolves: The type or types that this provider binds to.
            defaults to the return type annotation of the provided func
        :type resolves: Any, optional

        :param eager: If the binding eager, defaults to False
        :type eager: bool

        :return: Either a decorator or the unedited function supplied.
        """

        def wrapper(_func: FuncT) -> FuncT:
            if self.opened:
                raise SetupError("FlexGraph opened. Cannot be bound.")

            self._rules.add_binding(_func, resolves)
            self._rules.add_policy(_func, scope=scope, eager=eager)
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

        if self.opened:
            raise SetupError("FlexGraph opened. Cannot be bound.")

        self._rules.add_binding(func := lambda: value, resolves or type(value))
        self._rules.add_policy(func, scope="application", eager=True)
        return value

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

    @contextmanager
    def override(self) -> Iterator["FlexGraph"]:
        """
        This context manager is primarily intended for testing use-cases.

        An override allow users to override dependency bindings a temporary way
        which will be reverted when the override is closed. This prevents making
        permanent changes to a graph which is usually defined directly in the module.

        The previous rules for the graph are preserved by the context manager and
        a clone of them is placed into the active graph instance. When the context
        manager exits, the previous un-edited rules are re-applied to the graph.

        :return: ``ContextManager[FlexGraph]``.
        """

        if self.opened:
            raise SetupError("FlexGraph already opened. Cannot be overriden.")

        rules = self._rules
        try:
            self._rules = self._rules.clone()
            yield self
        finally:
            self._rules = rules
