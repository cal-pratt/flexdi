from typing import Any, Callable, Optional, TypeVar, Union, overload

from ._rules import FlexRules
from ._types import FuncT, ScopeName
from .errors import FlexError

T = TypeVar("T")


class BindableMixin:
    opened: bool = False
    _rules: FlexRules

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
                raise FlexError("FlexGraph opened. Cannot be bound.")

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
            raise FlexError("FlexGraph opened. Cannot be bound.")

        self._rules.add_binding(func := lambda: value, resolves or type(value))
        self._rules.add_policy(func, scope="application", eager=True)
        return value
