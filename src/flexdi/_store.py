from asyncio import Lock
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any, AsyncIterator, Dict, MutableMapping

from ._types import Func, Instance
from ._util import invoke_callable


class FlexStore:
    """
    A store is used by a scope to keep track of what objects it owns. It is
    also used to create the objects such that they can be manged in the stores
    stack. To ensure concurrency safety, updating the store uses locks to create
    a critical section that will ensure that multiple instances of an object are
    not created when sharing the application scope across multiple concurrent
    request scopes.
    """

    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._instances: MutableMapping[Func, Instance] = {}

        self._func_locks: Dict[Func, Lock] = {}
        self._main_lock = Lock()

    @asynccontextmanager
    async def lock(self, func: Func) -> AsyncIterator[None]:
        # Double check logic to ensure we don't create multiple locks
        # for the same callable.
        if func not in self._func_locks:
            async with self._main_lock:
                if func not in self._func_locks:
                    self._func_locks[func] = Lock()
        async with self._func_locks[func]:
            yield

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
