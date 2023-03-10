from typing import Any, Dict, List, Optional

from ._rules import FlexRules
from ._store import FlexStore
from ._types import Func, Instance, Openable, Resolver
from ._util import parse_signature


class FlexScope(Openable):
    """
    A scope in the storage mechanism and policy executor of dependencies.

    A scope used by the FlexGraph is created as a linked list:

    .. code-block:: text

        RequestScope -> ApplicationScope -> GraphScope.

    When an object is requested to be created, the scope will examine the policy
    on the dependency and see if it matches. If the policy is not correct for the
    current scope, it will defer creation to its parent scope. If no scope exists
    that can manage the dependency, an error will be raised.

    Each scope manages its cache of stored dependencies, to allow instances to be
    destroyed at a granular level. i.e. A higher level scope can be closed without
    closing the parent scope. An example of this would be request scoped dependencies
    such as database connection being closed per request, while connection pool
    objects are allowed to live for the full lifetime of the application.

    Each of the scope objects in the chain will share the same copy of the dependency
    tree to speed up the resolution of items, and allow validations on declared
    dependencies to only be performed once.

    If a dependency has an eager policy, and its scope policy matches the current
    scope, then the object will be instantiated as soon as the scope is opened.
    """

    def __init__(
        self,
        rules: FlexRules,
        parent: Optional["FlexScope"] = None,
        scope_names: Optional[List[str]] = None,
    ) -> None:
        self._rules = rules
        self._parent = parent
        self._scope_names = scope_names or []
        self._store = FlexStore()
        self.opened = False

    async def open(self) -> None:
        if self.opened:
            return

        try:
            self.opened = True
            for func, policy in self._rules.get_policies().items():
                if policy.eager and policy.scope in self._scope_names:
                    await self.evaluate(func)
        except:  # noqa: E722
            await self.close()
            raise

    async def close(self) -> None:
        try:
            if self.opened:
                await self._store.close()
        finally:
            self.opened = False

    async def evaluate(self, func: Func) -> Any:
        if not self._rules.has_binding(func):
            self._rules.add_binding(func, func)
            self._rules.validate()

        func = self._rules.get_binding(func)
        policy = self._rules.get_policy(func)

        if policy.scope not in self._scope_names:
            if parent := self._parent:
                return await parent.evaluate(func)
            else:
                raise Exception(
                    "Could not resolve scope for func "
                    f"{func} in scope {policy.scope}"
                )

        async with self._store.lock(func):
            if func not in self._store:
                args: Dict[str, Any] = {}
                for name, clazz in parse_signature(func).items():
                    args[name] = await self.evaluate(clazz)

                await self._store.create(func, args)

        return self._store[func]


class RequestScope(FlexScope, Resolver):
    """
    The request scope is the storage for all request or unmarked scoped dependencies.
    If already opened, it can be called repeatedly to have cached calls.
    """

    def __init__(self, rules: FlexRules, parent: FlexScope) -> None:
        super().__init__(rules, parent=parent, scope_names=["request"])

    async def _resolve(self, func: Func) -> Instance:
        if self.opened:
            return await self.evaluate(func)
        async with self:
            return await self.evaluate(func)


class ApplicationScope(FlexScope, Resolver):
    """
    The application scope is the storage for all application scoped dependencies.
    For higher stricter scoped dependencies it will defer to the request scope.
    """

    def __init__(self, rules: FlexRules, parent: FlexScope) -> None:
        super().__init__(rules, parent, scope_names=["application"])

    def request_scope(self) -> "RequestScope":
        if not self.opened:
            raise Exception("Scope must be opened before it can be chained")
        return RequestScope(self._rules.clone(), self)

    async def _resolve(self, func: Func) -> Instance:
        if self.opened:
            return await self.request_scope().resolve(func)
        async with self:
            return await self.request_scope().resolve(func)


class GraphScope(FlexScope, Resolver):
    """
    The base scope for a graph instance. Mainly exists to provide a nice container
    for the FlexGraph instance. This will defer to the application scope for
    constructing values.
    """

    async def open(self) -> None:
        if self.opened:
            return
        self._rules.validate()
        self.opened = True

    def application_scope(self) -> "ApplicationScope":
        if not self.opened:
            self._rules.validate()
            self.opened = True
        return ApplicationScope(self._rules.clone(), self)

    async def _resolve(self, func: Func) -> Instance:
        if self.opened:
            return await self.application_scope().resolve(func)
        async with self:
            return await self.application_scope().resolve(func)
