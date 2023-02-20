import inspect
from collections import ChainMap
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, MutableMapping

from .errors import CycleError


@dataclass
class Dependant:
    key: Any
    args: Dict[str, "Dependant"]
    func: Callable[..., Any]


@dataclass
class DependantCache:
    _cache: MutableMapping[Any, "Dependant"] = field(default_factory=dict)
    _constructing: set[Any] = field(default_factory=set)

    def __contains__(self, key: Any) -> bool:
        return key in self._cache

    def __getitem__(self, key: Any) -> Dependant:
        return self._cache[key]

    def __setitem__(self, key: Any, dep: Dependant) -> None:
        self._cache[key] = dep

    @contextmanager
    def cycle_guard(self, key: Any) -> Iterator[None]:
        if key in self._constructing:
            raise CycleError(f"Cycle Detected construction dependency for {key}")
        self._constructing.add(key)
        try:
            yield
        finally:
            self._constructing.remove(key)

    def chain(self) -> "DependantCache":
        return DependantCache(ChainMap({}, self._cache), set(self._constructing))


def create_dependant(
    key: Any,
    func: Callable[..., Any],
    *,
    cache: DependantCache,
    override: bool = False,
    store: bool = True,
) -> Dependant:
    if not override and key in cache:
        return cache[key]

    with cache.cycle_guard(key):
        signature = inspect.signature(func)
        res = Dependant(
            key=key,
            args={
                key: create_dependant(
                    key=param.annotation,
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
        cache[key] = res

    return res
