import inspect
from collections import ChainMap
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    MutableMapping,
    Optional,
    Set,
    Type,
    Union,
)

from .errors import CycleError, ImplicitBindingError
from .implicit import is_implicitbinding
from .util import determine_return_type, invoke_callable

# Note, in 3.10+ we can start using TypeAlias
Clazz = Type[Any]
Func = Union[Clazz, Callable[..., Any]]
Instance = Any


@dataclass
class Policy:
    eager: bool


DEFAULT_POLICY = Policy(eager=False)


def parse_signature(func: Func) -> Dict[str, Clazz]:
    arguments: Dict[str, Clazz] = {}
    for name, param in inspect.signature(func).parameters.items():
        if not param.annotation:
            raise Exception(f"No annotation on argument {func=} {name=}")
        arguments[name] = param.annotation

    return arguments


class FlexState:
    def __init__(self) -> None:
        self.opened = False
        self._stack: AsyncExitStack = AsyncExitStack()
        self._bindings: MutableMapping[Func, Func] = {}
        self._policies: MutableMapping[Func, Policy] = {}
        self._instances: MutableMapping[Func, Instance] = {}

    def chain(self) -> "FlexState":
        state = FlexState()
        state._bindings = ChainMap({}, self._bindings)
        state._policies = ChainMap({}, self._policies)
        state._instances = ChainMap({}, self._instances)
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
        self._policies[func] = Policy(eager=eager)

    def get_policy(self, func: Func) -> Policy:
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
        self._instances.clear()
        try:
            await self._stack.aclose()
        finally:
            self.opened = False

    async def resolve(self, func: Func) -> Any:
        if func not in self._bindings:
            self.add_binding(func, func)
            self.validate()

        return await self._resolve(self._bindings[func])

    async def _resolve(self, func: Func) -> Any:
        if func in self._instances:
            return self._instances[func]

        args: Dict[str, Any] = {}
        for name, annotation in parse_signature(func).items():
            alias = self._bindings.get(annotation, annotation)
            args[name] = await self._resolve(alias)

        instance = await invoke_callable(stack=self._stack, func=func, args=args)
        self._instances[func] = instance
        return instance
