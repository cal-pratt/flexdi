import inspect
from collections import ChainMap
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, MutableMapping, Set, Type

from .binding import Binding, BindingMap, create_binding
from .errors import CycleError


@dataclass
class Dependant:
    target: Type[Any]
    args: Dict[str, "Dependant"]
    func: Callable[..., Any]


@dataclass
class DependantMap:
    _map: MutableMapping[Type[Any], "Dependant"] = field(default_factory=dict)
    _constructing: Set[Type[Any]] = field(default_factory=set)

    def chain(self) -> "DependantMap":
        return DependantMap(ChainMap({}, self._map), set(self._constructing))

    def __contains__(self, target: Type[Any]) -> bool:
        return target in self._map

    def __getitem__(self, target: Type[Any]) -> Dependant:
        return self._map[target]

    def __setitem__(self, target: Type[Any], dep: Dependant) -> None:
        self._map[target] = dep

    def clear(self) -> None:
        self._map.clear()

    @contextmanager
    def cycle_guard(self, target: Type[Any]) -> Iterator[None]:
        if target in self._constructing:
            raise CycleError(f"Cycle Detected construction dependency for {target}")
        self._constructing.add(target)
        try:
            yield
        finally:
            self._constructing.remove(target)


def create_dependant(
    *,
    binding: Binding,
    bindings: BindingMap,
    dependants: DependantMap,
    use_cached: bool = True,
    update_cached: bool = True,
) -> Dependant:
    if use_cached and binding.target in dependants:
        return dependants[binding.target]

    with dependants.cycle_guard(binding.target):
        signature = inspect.signature(binding.func)
        dependant = Dependant(
            target=binding.target,
            args={
                name: create_dependant(
                    binding=create_binding(
                        func=param.annotation,
                        eager=binding.eager,
                        bindings=bindings,
                    ),
                    bindings=bindings,
                    dependants=dependants,
                )
                for name, param in signature.parameters.items()
            },
            func=binding.func,
        )

    if update_cached:
        dependants[binding.target] = dependant

    return dependant
