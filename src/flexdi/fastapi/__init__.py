from contextlib import AsyncExitStack
from typing import Any, AsyncIterator, Optional, Type, TypeVar, cast

from fastapi import Depends, FastAPI, Request

from flexdi import ApplicationScope, FlexGraph, RequestScope

T = TypeVar("T")


def FlexDepends(target: Type[T]) -> T:
    async def depends(request: Request) -> Any:
        scope: Optional[RequestScope] = getattr(request, "_flex_scope", None)
        if not scope:
            raise Exception("FastAPIGraph not attached to app")
        return await scope.resolve(target)

    return cast(T, Depends(depends))


class FastAPIGraph(FlexGraph):
    def __init__(self, app: FastAPI) -> None:
        super().__init__()
        stack = AsyncExitStack()

        app_scope: ApplicationScope = None  # type: ignore

        async def attach_flex(request: Request) -> AsyncIterator[None]:
            async with app_scope.request_scope() as request_scope:
                setattr(request, "_flex_scope", request_scope)
                yield

        app.router.dependencies.insert(0, Depends(attach_flex))

        @app.on_event("startup")
        async def startup() -> None:
            await self.open()
            stack.push_async_callback(self.close)
            nonlocal app_scope
            app_scope = self.application_scope()
            await app_scope.open()
            stack.push_async_callback(app_scope.close)

        @app.on_event("shutdown")
        async def shutdown() -> None:
            await stack.aclose()


__all__ = ["FlexDepends", "FastAPIGraph"]
