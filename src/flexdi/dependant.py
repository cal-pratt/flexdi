import inspect
from collections import ChainMap
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, MutableMapping, Type

from .errors import CycleDetectionError


@dataclass
class Dependant:
    key: Type[Any]
    args: dict[str, "Dependant"]
    func: Callable[..., Any]


@dataclass
class DependantCache:
    _cache: MutableMapping[Type[Any], "Dependant"] = field(default_factory=dict)
    _constructing: set[Type[Any]] = field(default_factory=set)

    def __contains__(self, key: Type[Any]) -> bool:
        return key in self._cache

    def __getitem__(self, key: Type[Any]) -> Dependant:
        return self._cache[key]

    def __setitem__(self, key: Type[Any], dep: Dependant) -> None:
        self._cache[key] = dep

    @contextmanager
    def cycle_guard(self, key: Type[Any]) -> Iterator[None]:
        if key in self._constructing:
            raise CycleDetectionError("Cycle Detected")
        self._constructing.add(key)
        try:
            yield
        finally:
            self._constructing.remove(key)

    def chain(self) -> "DependantCache":
        return DependantCache(ChainMap({}, self._cache), set(self._constructing))


def create_dependant(
    clazz: Type[Any],
    func: Callable[..., Any],
    *,
    cache: DependantCache,
    override: bool = False,
    store: bool = True,
) -> Dependant:
    if not override and clazz in cache:
        return cache[clazz]

    with cache.cycle_guard(clazz):
        signature = inspect.signature(func)
        res = Dependant(
            key=clazz,
            args={
                key: create_dependant(
                    clazz=param.annotation,
                    func=param.annotation,
                    cache=cache,
                    override=False,
                    store=True,
                )
                for key, param in signature.parameters.items()
            },
            func=func,
        )
    if store:
        cache[clazz] = res

    return res
