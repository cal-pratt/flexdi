import asyncio
import sys
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from flexdi import FlexGraph

graph = FlexGraph()


@graph.bind
async def provide_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite://")
    try:
        yield engine
    finally:
        await engine.dispose()


@graph.bind
async def provide_connection(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    async with engine.begin() as conn:
        yield conn


async def execute(conn: AsyncConnection) -> int:
    print((await conn.execute(text("SELECT datetime('now');"))).one())
    return 0


# If already within an async context, then you can use the
# async versions of the graph methods.
async def main() -> int:
    async with graph:
        return await graph.aresolve(execute)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
