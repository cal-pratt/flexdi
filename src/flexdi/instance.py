import inspect
from collections import ChainMap
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any, MutableMapping, Type

from .dependant import Dependant, DependantMap


@dataclass
class InstanceMap:
    _map: MutableMapping[Type[Any], Any] = field(default_factory=dict)

    def chain(self) -> "InstanceMap":
        return InstanceMap(ChainMap({}, self._map))

    def __contains__(self, target: Type[Any]) -> bool:
        return target in self._map

    def __getitem__(self, target: Type[Any]) -> Any:
        return self._map[target]

    def __setitem__(self, target: Type[Any], value: Any) -> None:
        self._map[target] = value

    def clear(self) -> None:
        self._map.clear()


async def create_instance(
    *,
    dependant: Dependant,
    instances: InstanceMap,
    dependants: DependantMap,
    stack: AsyncExitStack,
    use_cached: bool = True,
    update_cached: bool = True,
) -> Any:
    if use_cached and dependant.target in instances:
        return instances[dependant.target]

    kwargs = {
        name: await create_instance(
            dependant=subdep,
            instances=instances,
            dependants=dependants,
            stack=stack,
        )
        for name, subdep in dependant.args.items()
    }

    if inspect.isasyncgenfunction(dependant.func):
        context_func = asynccontextmanager(dependant.func)
        instance = await stack.enter_async_context(context_func(**kwargs))
    elif inspect.isgeneratorfunction(dependant.func):
        context_func = contextmanager(dependant.func)  # type: ignore
        instance = stack.enter_context(context_func(**kwargs))  # type: ignore
    elif inspect.iscoroutinefunction(dependant.func):
        instance = await dependant.func(**kwargs)
    else:
        instance = dependant.func(**kwargs)

    if update_cached:
        instances[dependant.target] = instance

    return instance
