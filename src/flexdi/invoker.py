import inspect
from collections import ChainMap
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any, MutableMapping, Type

from .dependant import Dependant


@dataclass
class CallCache:
    _cache: MutableMapping[Type[Any], Any] = field(default_factory=dict)

    def __contains__(self, key: Type[Any]) -> bool:
        return key in self._cache

    def __getitem__(self, key: Type[Any]) -> Any:
        return self._cache[key]

    def __setitem__(self, key: Type[Any], value: Any) -> None:
        self._cache[key] = value

    def chain(self) -> "CallCache":
        return CallCache(ChainMap({}, self._cache))


async def call_dependant(
    dep: Dependant, *, cache: CallCache, stack: AsyncExitStack, override: bool = False, store: bool = True
) -> Any:
    if not override and dep.key in cache:
        return cache[dep.key]

    kwargs = {
        name: await call_dependant(subdep, cache=cache, stack=stack, override=False, store=True)
        for name, subdep in dep.args.items()
    }

    if inspect.isasyncgenfunction(dep.func):
        context_func = asynccontextmanager(dep.func)
        res = await stack.enter_async_context(context_func(**kwargs))
    elif inspect.isgeneratorfunction(dep.func):
        context_func = contextmanager(dep.func)  # type: ignore
        res = stack.enter_context(context_func(**kwargs))  # type: ignore
    elif inspect.iscoroutinefunction(dep.func):
        res = await dep.func(**kwargs)
    else:
        res = dep.func(**kwargs)

    if store:
        cache[dep.key] = res

    return res
