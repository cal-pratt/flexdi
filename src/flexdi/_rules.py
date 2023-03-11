from collections import ChainMap
from dataclasses import dataclass
from typing import Dict, Iterable, List, MutableMapping, Optional, Set, Union

from ._implicit import is_implicitbinding
from ._types import SCOPE_NAMES, Func, ScopeName
from ._util import determine_return_type, parse_signature
from .errors import CycleError, FlexError, ImplicitBindingError


@dataclass
class FlexPolicy:
    scope: ScopeName
    eager: bool


DEFAULT_POLICY = FlexPolicy(scope="request", eager=False)


class FlexRules:
    """
    Rules determine the validity of a callable to be injected and also keep track
    of bindings, which allow callables to specify different providers. When scopes
    create objects they will look to the rules to find the appropriate callables
    to invoke for callables and their dependencies. After adding bindings and
    policies to the rules, make sure to have them validated.
    """

    def __init__(self) -> None:
        self._validated = True
        self._bindings: MutableMapping[Func, Func] = {}
        self._policies: MutableMapping[Func, FlexPolicy] = {}

    def clone(self) -> "FlexRules":
        self.validate()
        state = FlexRules()
        state._bindings = ChainMap({}, self._bindings)
        state._policies = ChainMap({}, self._policies)
        return state

    def add_binding(
        self,
        func: Func,
        aliases: Optional[Union[Func, List[Func]]] = None,
    ) -> None:
        """Set the alias to be resolved as a clazz"""
        if aliases is None:
            aliases = [determine_return_type(func)]
        elif not isinstance(aliases, Iterable):
            aliases = [aliases]
        for alias in aliases:
            self._bindings[alias] = func
        self._validated = False

    def has_binding(self, func: Func) -> bool:
        return func in self._bindings

    def get_binding(self, func: Func) -> Func:
        return self._bindings[func]

    def add_policy(
        self,
        func: Func,
        scope: ScopeName,
        eager: bool,
    ) -> None:
        if scope not in SCOPE_NAMES:
            raise FlexError(f"Invalid scope name {scope}")
        self._policies[func] = FlexPolicy(scope=scope, eager=eager)
        self._validated = False

    def get_policy(self, func: Func) -> FlexPolicy:
        return self._policies.get(func, DEFAULT_POLICY)

    def get_policies(self) -> Dict[Func, FlexPolicy]:
        return {func: self.get_policy(func) for func in self._bindings.values()}

    def reduce_bindings(self) -> None:
        """
        Reduce the set of aliases down into flat mappings. e.g.

        Before: (a -> b), (b -> c), (c -> d), (d -> d)
        After:  (a -> d), (b -> d), (c -> d), (d -> d)
        """

        for clazz, func in set(self._bindings.items()):
            stack: List[Func] = [func]
            seen: Set[Func] = {func}
            while func != self._bindings.get(func, func):
                func = self._bindings[func]
                stack.append(func)
                if func in seen:
                    stack_error = "".join(f"\n  {s}" for s in stack)
                    raise CycleError(f"Cycle detected in dependencies: {stack_error}")
                seen.add(func)
            self._bindings[clazz] = func

    def validate_bindings(self) -> None:
        """
        Assert that the arguments declared by the provider funcs can be resolved
        by the current bindings in the state.
        """

        queue: Set[Func] = set(self._bindings.values())
        seen: Set[Func] = set()
        while queue:
            func = queue.pop()
            if func in seen:
                continue
            seen.add(func)

            for name, clazz in parse_signature(func).items():
                if clazz in self._bindings:
                    continue
                if not is_implicitbinding(clazz):
                    raise ImplicitBindingError(
                        "Unable to determine provider for argument "
                        f"{name}: {clazz} while evaluating {func}"
                    )
                self.add_binding(clazz, clazz)
                queue.add(clazz)

    def validate_bindings_acyclic(self) -> None:
        """
        Assert that for all the providers present there are no cycles present.
        """

        validated: Set[Func] = set()
        calculating: Set[Func] = set()
        stack: List[Func] = []

        def assert_acyclic(func: Func) -> None:
            stack.append(func)
            try:
                if func in validated:
                    return
                if func in calculating:
                    stack_error = "".join(f"\n  {s}" for s in stack)
                    raise CycleError(f"Cycle detected in dependencies: {stack_error}")

                calculating.add(func)

                for clazz in parse_signature(func).values():
                    assert_acyclic(self._bindings[clazz])

                validated.add(func)
            finally:
                stack.pop()

        for f in set(self._bindings.values()):
            assert_acyclic(f)

    def upgrade_scopes(self) -> None:
        """
        Sub dependencies of application scoped bindings should be upgraded to
        application scope to ensure that they are no created independently in
        each scope.
        """

        validated: Set[Func] = set()

        def upgrade_scope(func: Func) -> None:
            if func in validated:
                return

            self.get_policy(func).scope = "application"
            for clazz in parse_signature(func).values():
                upgrade_scope(self._bindings[clazz])

            validated.add(func)

        for f, p in self._policies.items():
            if p.scope == "application":
                upgrade_scope(f)

    def validate(self) -> None:
        if not self._validated:
            self.reduce_bindings()
            self.validate_bindings()
            self.validate_bindings_acyclic()
            self.upgrade_scopes()
        self._validated = True
