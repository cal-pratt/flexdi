from typing import AsyncIterator

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from flexdi.fastapi import FastAPIGraph, FlexDepends

# Creating the graph with reference to the FastAPI app binds the graph to the
# startup and shutdown events of the server, and enables FlexDepends values to
# be resolvable from the request context.
app = FastAPI()
graph = FastAPIGraph(app)


# Setting this dependency as application scopes will mean that it gets created
# once during the lifetime of the server, and will be re-used for every request.
# Anything that is application scoped MUST be thread-safe if you are going to use
# it from non asyncio endpoints.
@graph.bind(scope="application", eager=True)
async def provide_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite:///mydb.db")
    try:
        yield engine
    finally:
        await engine.dispose()


# Here the connection dependency is not set to application scoped.
# It will be created uniquely for each request we get.
@graph.bind
async def provide_connection(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    async with engine.begin() as conn:
        yield conn


# FlexDepends will make fastapi defer to the FlexGraph for creating the instance.
@app.get("/")
async def get(conn: AsyncConnection = FlexDepends(AsyncConnection)) -> list[str]:
    statement = text("SELECT name FROM sqlite_master;")
    return [table_name for [table_name] in await conn.execute(statement)]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5007)
