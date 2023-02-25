from typing import Any, AsyncIterator, Optional, Type, TypeVar, cast

from fastapi import Depends, FastAPI, Request

from flexdi import FlexGraph

T = TypeVar("T")


def FlexDepends(target: Type[T]) -> T:
    async def depends(request: Request) -> Any:
        graph: Optional[FlexGraph] = getattr(request, "_flex_graph", None)
        if not graph:
            raise Exception("FastAPIGraph not attached to app")
        return await graph.resolve(target)

    return cast(T, Depends(depends))


class FastAPIGraph(FlexGraph):
    def __init__(self, app: FastAPI) -> None:
        super().__init__()
        app.router.dependencies.insert(0, Depends(self.attach_flex))
        app.on_event("startup")(self.open)
        app.on_event("shutdown")(self.close)

    async def attach_flex(self, request: Request) -> AsyncIterator[None]:
        async with self.chain() as graph:
            setattr(request, "_flex_graph", graph)
            yield


__all__ = ["FlexDepends", "FastAPIGraph"]
