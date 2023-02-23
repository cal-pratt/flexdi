from collections import ChainMap
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, MutableMapping, Optional, Tuple, Type

from .util import determine_return_type


@dataclass
class Binding:
    target: Type[Any]
    func: Callable[..., Any]
    eager: bool


@dataclass
class BindingMap:
    _map: MutableMapping[Type[Any], Binding] = field(default_factory=dict)

    def chain(self) -> "BindingMap":
        return BindingMap(ChainMap({}, self._map))

    def __contains__(self, target: Type[Any]) -> bool:
        return target in self._map

    def __getitem__(self, target: Type[Any]) -> Binding:
        return self._map[target]

    def __setitem__(self, target: Type[Any], binding: Binding) -> None:
        self._map[target] = binding

    def items(self) -> Iterator[Tuple[Type[Any], Binding]]:
        yield from self._map.items()


def create_binding(
    *,
    func: Callable[..., Any],
    target: Optional[Type[Any]] = None,
    eager: bool = False,
    bindings: BindingMap,
    use_cached: bool = True,
    update_cached: bool = True,
) -> Binding:
    target = target or determine_return_type(func)

    if use_cached and target in bindings:
        return bindings[target]

    binding = Binding(
        target=target,
        func=func,
        eager=eager,
    )

    if update_cached:
        bindings[target] = binding

    return binding
