Overview
========

``flexdi`` offers a construct called the ``FlexGraph`` which is used to
keep track of dependencies and invoke other callables.

When determining dependencies for a callable, ``flexdi`` will examine the type
annotations of the arguments, and populate the graph with dependencies which can
satisfy the callable. A callable can be anything from a class (as seen with the
type annotations), to functions, class methods, generators, etc.

For complex types, ``flexdi`` allows binding helper functions that can map a
type definition to an instance. These bindings can themselves be injected
with dependencies. Bindings can also be defined as generators which allows
supplying custom teardown logic for dependencies.

Example Usage
-------------

A simple example of an application with SQLAlchemy dependencies:

.. code:: python

   import sys
   from typing import Iterator
   from sqlalchemy import Engine, create_engine, text
   from sqlalchemy.orm import Session

   from flexdi import FlexGraph

   # The FlexGraph keeps track of what dependencies different
   # providers require, and will later be used to resolve them.
   graph = FlexGraph()

   # Anything that requires an Engine will fetch it from provide_engine
   # For simple functions we infer the binding from the return type annotation.
   @graph.bind
   def provide_engine() -> Engine:
       return create_engine("sqlite://")


   # Generator responses can also be inferred. e.g.
   # - A function returning Iterator[T] binds to T
   # - A function returning AsyncIterator[T] binds to T
   @graph.bind
   def provide_session(engine: Engine) -> Iterator[Session]:
       with Session(engine) as session:
           yield session


   # We don't need to add any flexdi setup to our actual code.
   def main(session: Session) -> int:
       print(session.execute(text("SELECT now()")))
       return 0


   if __name__ == "__main__":
       # Start up the injector, and guard using a with statement to
       # ensure that we clean up any dependencies which require it
       with graph:
           sys.exit(graph.resolve(main))

The same example, but using async code:

.. code:: python

   import sys
   from typing import AsyncIterator
   from sqlalchemy.ext.asyncio import (
       AsyncConnection,
       AsyncEngine,
       create_async_engine
   )
   from sqlalchemy import text

   from flexdi import FlexGraph

   graph = FlexGraph()


   @graph.bind
   async def provide_engine() -> AsyncIterator[AsyncEngine]:
       engine = create_async_engine("sqlite://")
       try:
           yield engine
       finally:
           await engine.dispose()


   @graph.bind
   async def provide_connection(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
       async with engine.begin() as conn:
           yield conn


   async def main(conn: AsyncConnection) -> int:
       print(await conn.execute(text("SELECT now()")))
       return 0


   if __name__ == "__main__":
       with graph:
           # The injector can handle invoking async functions natively,
           # so no worry about adding in extra logic here.
           sys.exit(graph.resolve(main))
   ...


   # If already within an async context, then you can use the
   # async versions of these methods.
   async def func() -> int:
       async with graph:
           return await graph.aresolve(main)
