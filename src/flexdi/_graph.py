from contextlib import contextmanager
from typing import Iterator, TypeVar

from ._bindable import BindableMixin
from ._entrypoint import EntrypointMixin
from ._rules import FlexRules
from ._scope import ApplicationScope
from ._types import Func, Instance

T = TypeVar("T")


class FlexGraph(BindableMixin, EntrypointMixin):
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
        self._rules = FlexRules()

    def application_scope(self) -> ApplicationScope:
        return ApplicationScope(self._rules.clone())

    async def _resolve(self, func: Func) -> Instance:
        return await self.application_scope().resolve(func)

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

        rules = self._rules
        try:
            self._rules = self._rules.clone()
            yield self
        finally:
            self._rules = rules
