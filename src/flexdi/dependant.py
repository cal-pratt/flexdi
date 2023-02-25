from collections import ChainMap
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, MutableMapping, Set, Type

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
