from collections import ChainMap
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Set, Union

from .errors import CycleError, ImplicitBindingError
from .implicit import is_implicitbinding
from .policy import DEFAULT_POLICY, FlexPolicy
from .store import FlexStore
from .types import Func
from .util import determine_return_type, parse_signature


class FlexState:
    def __init__(self) -> None:
        self.opened = False
        self._store = FlexStore()
        self._bindings: MutableMapping[Func, Func] = {}
        self._policies: MutableMapping[Func, FlexPolicy] = {}

    def chain(self) -> "FlexState":
        state = FlexState()
        state._store = self._store.chain()
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

    def add_policy(
        self,
        func: Func,
        eager: bool,
    ) -> None:
        self._policies[func] = FlexPolicy(eager=eager)

    def get_policy(self, func: Func) -> FlexPolicy:
        return self._policies.get(func, DEFAULT_POLICY)

    def reduce_bindings(self) -> None:
        """
        Reduce the set of aliases down into flat mappings. e.g.

        Before: (a -> b), (b -> c), (c -> d), (d -> d)
        After:  (a -> d), (b -> d), (c -> d), (d -> d)
        """

        for clazz, func in set(self._bindings.items()):
            while func != self._bindings.get(func, func):
                func = self._bindings[func]
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

    def validate(self) -> None:
        self.reduce_bindings()
        self.validate_bindings()
        self.validate_bindings_acyclic()

    async def open(self) -> "FlexState":
        if self.opened:
            return self

        self.validate()
        try:
            self.opened = True
            for func in self._bindings.values():
                policy = self.get_policy(func)
                if policy.eager:
                    await self._resolve(func)
        except:  # noqa: E722
            await self.close()
            raise
        return self

    async def close(self) -> None:
        try:
            await self._store.close()
        finally:
            self.opened = False

    async def resolve(self, func: Func) -> Any:
        if func not in self._bindings:
            self.add_binding(func, func)
            self.validate()

        return await self._resolve(self._bindings[func])

    async def _resolve(self, func: Func) -> Any:
        async with self._store.lock(func):
            if func not in self._store:
                args: Dict[str, Any] = {}
                for name, annotation in parse_signature(func).items():
                    alias = self._bindings.get(annotation, annotation)
                    args[name] = await self._resolve(alias)

                await self._store.create(func, args)

        return self._store[func]
