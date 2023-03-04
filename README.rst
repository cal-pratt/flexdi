
Flex DI
=======

.. image:: https://img.shields.io/pypi/v/flexdi.svg
   :target: https://pypi.org/project/flexdi/

.. image:: https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fcal-pratt%2Fflexdi%2Fbadge%3Fref%3Dmain&style=flat
   :target: https://github.com/cal-pratt/flexdi/actions

.. image:: https://readthedocs.org/projects/flexdi/badge/?version=latest
   :target: https://flexdi.readthedocs.io


``flexdi`` is a yet another Dependency Injection library for Python.
``flexdi`` provides a lightweight alternative to common DI solutions
with minimal setup to be included in your projects. This library is
intended for use with type annotated Python libraries, as it leverages
these type annotations to perform injection.

.. note::
  | **Flex DI is still a work in progress and is not yet intended
    for production use-cases.**
  | **Be aware that APIs are likely to change in upcoming releases.**


|
| The full documentation is available at `flexdi.readthedocs.io <https://flexdi.readthedocs.io>`_.

Goals
-----

- | **Minimal Setup**
  | Minimize boilderplate by leveraging type annotations to resolve
    arguments. Allows user code to remain generic and reusable.

- | **Inject Any Callable**
  | Provide any typed callable as an input to be invoked.
    Supports sync and async callables.

- | **Resource Management**
  | Define dependencies as context managers and have
    their startup and shutdown logic invoked in a reliable order.
    Supports sync and async context managers.

- | **Scoped Dependencies**
  | Clearly define dependency lifetimes.
    Use ``"application"`` scoped dependencies to provide singleton like objects.
    Use ``"request"`` scoped dependencies to allow short-term isolated usage.


Overview
========

``flexdi`` offers the ``FlexGraph``, used to manage dependencies and invoke callables.
The graph is a representation of what dependencies exist, and what providers can be
used to fulfil them.

When determining dependencies for a callable, ``flexdi`` will examine the type
annotations of the arguments to populate the graph with dependencies that can
satisfy the callable. A callable can be anything from a class, to functions, 
class methods, generators, etc.

``flexdi`` allows *binding* helper functions to the graph as a providers of types,
determined by their return annotations.
Bindings can themselves be injected with dependencies,
determined by their parameter annotations.
A Binding can be a simple function or a generator with custom teardown logic.

Example Usage
-------------

A simple example of an application with SQLAlchemy dependencies:

.. code:: python

    from typing import Iterator
    
    from sqlalchemy import Engine, create_engine, text
    from sqlalchemy.orm import Session
    
    from flexdi import FlexGraph
    
    # The FlexGraph keeps track of what dependencies different
    # providers require, and will later be used to resolve them.
    graph = FlexGraph()
    
    
    # Let's add a binding for an Engine.
    # The binding will be used for anything that requires an Engine.
    # FlexGraph uses the return type annotation to create bindings.
    @graph.bind
    def provide_engine() -> Engine:
        return create_engine("sqlite:///mydb.db")
    
    
    # Generator responses can also be used. e.g.
    # - A function returning Iterator[T] binds to T
    # - A function returning Generator[T, U, V] binds to T
    # - A function returning AsyncIterator[T] binds to T
    # - A function returning AsyncGenerator[T, U] binds to T
    @graph.bind
    def provide_connection(engine: Engine) -> Iterator[Session]:
        with Session(engine) as session:
            yield session
    
    
    # An entrypoint is a convenience method for a creating no argument
    # version of a function or coroutine. You should typically only
    # have one entrypoint used in your applications.
    @graph.entrypoint
    def main(conn: Session) -> None:
        statement = text("SELECT name FROM sqlite_master;")
        for [table_name] in conn.execute(statement):
            print(table_name)
    
    
    # Notice that we call main with no arguments!
    if __name__ == "__main__":
        main()
    

The same example, but using async code:

.. code:: python

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


Want to make a contribution?
----------------------------

See `CONTRIBUTING.md <https://github.com/cal-pratt/flexdi/blob/main/CONTRIBUTING.md>`_
