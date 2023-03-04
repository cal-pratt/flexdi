from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from flexdi import FlexGraph

graph = FlexGraph()


@graph.bind
async def provide_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite:///mydb.db")
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
    statement = text("SELECT name FROM sqlite_master;")
    for [table_name] in await conn.execute(statement):
        print(table_name)


if __name__ == "__main__":
    main()
