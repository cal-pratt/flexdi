from asyncio import Lock
from collections import ChainMap
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any, AsyncIterator, Dict, MutableMapping

from .types import Func, Instance
from .util import invoke_callable


class FlexStore:
    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._instances: MutableMapping[Func, Instance] = {}

        self._func_locks: Dict[Func, Lock] = {}
        self._main_lock = Lock()

    @asynccontextmanager
    async def lock(self, func: Func) -> AsyncIterator[None]:
        if func not in self._func_locks:
            async with self._main_lock:
                if func not in self._func_locks:
                    self._func_locks[func] = Lock()
        async with self._func_locks[func]:
            yield

    def chain(self) -> "FlexStore":
        store = FlexStore()
        store._instances = ChainMap({}, self._instances)
        return store

    def __contains__(self, func: Func) -> bool:
        return func in self._instances

    def __getitem__(self, func: Func) -> Instance:
        return self._instances[func]

    async def close(self) -> None:
        self._instances.clear()
        await self._stack.aclose()

    async def create(self, func: Func, args: Any) -> None:
        self._instances[func] = await invoke_callable(
            stack=self._stack, func=func, args=args
        )
