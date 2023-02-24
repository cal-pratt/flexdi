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


@graph.entrypoint
async def main(conn: AsyncConnection) -> None:
    print((await conn.execute(text("SELECT datetime('now');"))).one())


if __name__ == "__main__":
    sys.exit(main())
