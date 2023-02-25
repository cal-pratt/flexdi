from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, MutableMapping, Tuple, Type


@dataclass
class Binding:
    target: Type[Any]
    func: Callable[..., Any]
    eager: bool


@dataclass
class BindingMap:
    _map: MutableMapping[Type[Any], Binding] = field(default_factory=dict)

    def chain(self) -> "BindingMap":
        return BindingMap({**self._map})

    def __contains__(self, target: Type[Any]) -> bool:
        return target in self._map

    def __getitem__(self, target: Type[Any]) -> Binding:
        return self._map[target]

    def __setitem__(self, target: Type[Any], binding: Binding) -> None:
        self._map[target] = binding

    def __delitem__(self, target: Type[Any]) -> None:
        del self._map[target]

    def items(self) -> Iterator[Tuple[Type[Any], Binding]]:
        yield from self._map.items()
