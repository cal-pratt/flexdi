
FlexDI
======

.. image:: https://img.shields.io/pypi/v/flexdi.svg
   :target: https://pypi.org/project/flexdi/

.. image:: https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fcal-pratt%2Fflexdi%2Fbadge%3Fref%3Dmain&style=flat
   :target: https://github.com/cal-pratt/flexdi/actions

.. image:: https://readthedocs.org/projects/flexdi/badge/?version=latest
   :target: https://flexdi.readthedocs.io


``flexdi`` is a yet another dependency injection library for Python.
``flexdi`` provides a lightweight alternative to common DI solutions
with minimal setup to be included in your projects. This library is
intended for use with type annotated Python libraries, as it leverages
these type annotations to perform injection.

.. note::
  | **FlexDI is still a work in progress and is not yet intended
    for production use-cases.**
  | **Be aware that APIs are likely to change in upcoming releases.**

|
| The full documentation is available at `flexdi.readthedocs.io <https://flexdi.readthedocs.io>`_.

Goals
-----

- | **Minimal Setup**
  | ``flexdi`` minimizes setup by leveraging type annotations to perform
    injection, allowing user code to remain generic and reusable.
    The avoids library lock-in which can be prevalent in other DI systems.

- | **Inject Any Callable**
  | In ``flexdi``, you can provide any typed callable as an input to be invoked.
    This avoids having to make class definitions purely for injection to work.

- | **Resource Management**
  | Dependencies in ``flexdi`` can be defined as context managers and will have
    their startup and shutdown logic invoked in a reliable order.

- | **Asyncio Support**
  | ``flexdi`` supports calling both sync and async callables, and allows
    defining dependencies as sync or async context managers.

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
    
    
    # Let's add a binding for an Engine. Anything that requires an Engine will
    # now fetch it from provide_engine.
    # FlexGraph uses the functions return type annotation to perform the binding.
    @graph.bind
    def provide_engine() -> Engine:
        return create_engine("sqlite://")
    
    
    # Generator responses can also be used. e.g.
    # - A function returning Iterator[T] binds to T
    # - A function returning AsyncIterator[T] binds to T
    @graph.bind
    def provide_session(engine: Engine) -> Iterator[Session]:
        with Session(engine) as session:
            yield session
    
    
    def execute(session: Session) -> int:
        print(session.execute(text("SELECT datetime('now');")).one())
        return 0
    
    
    # We always call the graph from a with statement to ensure
    # we clean up any dependencies which require teardown
    def main() -> int:
        with graph:
            return graph.resolve(main)
    
    
    if __name__ == "__main__":
        sys.exit(main())
    

The same example, but using async code:

.. code:: python

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
    

Alternatives
------------

Although there are many, many other dependency injection libraries, I found that
I was still left looking for more lightweight/minimal solutions to this problem. 
My thoughts on some of the popular alternatives I have used in the past:

- | `dependency-injector <https://github.com/ets-labs/python-dependency-injector>`_
  | This library is probably the most mature out of all the alternatives.
    Its main driving principal is that "Explicit is better than
    implicit", in that you need to specify explicitly how to assemble/
    inject the dependencies. ``flexdi`` is still explicit in the sense
    that dependencies are directly referenced from their type
    annotations, and by leveraging them we can avoid a lot of the more
    verbose setup required in ``DeclarativeContainer`` structures.

- | `fastapi <https://github.com/tiangolo/fastapi>`_
  | This web framework provides an excellent way to perform dependency injection,
    but it does not provide a way to perform dependency injection outside
    the context of web request. When configuring the injection, you must
    also provide default values to arguments, which ties application code
    to the web framework, making it more difficult to re-use code in
    other contexts. Additionally, it does not provide rich support for
    lifetime/singleton scoped dependencies, making the setup of some
    dependencies increasingly awkward.

- | `pinject <https://github.com/google/pinject>`_
  | This library allows you to perform DI with minimal setup, but its major
    downfall is that it relies on the names of arguments to perform injection.
    If the name of the argument does not match the name of the class, then
    you are forced to bind it explicitly. If there are multiple objects
    that specify a dependency of a particular type, but use different
    names, then you need to bind them all individually as well. And
    sadly, this project has now been archived and is read-only.

