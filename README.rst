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


The full documentation is available at `flexdi.readthedocs.io <https://flexdi.readthedocs.io>`_.

Goals
-----

- | **Minimal Setup**
  | Some DI systems require that you conform to a particular style of class
    definition, a naming convention to arguments, placing wrappers around class
    or method definitions, or providing complex default arguments which are tied
    to the DI system.
    ``flexdi`` mainly uses type annotations to perform injection, which avoids
    a common problem of library lock-in where frameworks force you to design
    components using their highly specialized constructs.

- | **Inject Any Callable**
  | Basic Python DI tools only allow classes to be used for injection, which can
    be quite limiting. In ``flexdi``, you can provide any typed callable as an
    input to be invoked.
    This avoids having to make class definitions purely for injection to work.

- | **Lifetime Management**
  | When creating dependencies for your callable, you often have resources that
    need to be properly torn down when your work is done. Providers for types in
    ``flexdi`` can be initialized using context managers that will have their
    shutdown logic invoked when you're done your work.

- | **Asyncio Support**
  | ``flexdi`` allows calling both sync and async methods directly, and provides
    both a sync and async interface to its main invocation method. Similarly,
    dependency providers may be defined as async methods, or be provided as
    async context managers.

Overview
========

``flexdi`` offers a construct called the ``FlexPack`` which is used to
inject callables with arguments and invoke these callables. These
arguments are dependencies you want to inject in your application.

When determining dependencies for a callable, ``flexdi`` will examine
the type annotations of the arguments, and construct a graph of objects
which can satisfy the callable. A callable can be anything from a class
(as seen with the type annotations), to functions, class methods,
generators, etc.

For complex types, ``flexdi`` allows binding helper functions that can
map an instance to a type definition. These helper functions can
themselves be injected with dependencies. Bindings can also be defined
as generators which allows supplying custom teardown logic for your
dependencies.

Example Usage
-------------

A simple example of an application with SQLAlchemy dependencies:

.. code:: python

   import sys
   from typing import Iterator
   from sqlalchemy import Engine, create_engine, text
   from sqlalchemy.orm import Session

   from flexdi import FlexPack

   flex = FlexPack()

   # Anything that requires an Engine will fetch it from provide_engine
   # For simple functions we infer the binding from the return type annotation.
   @flex.bind
   def provide_engine() -> Engine:
       return create_engine("sqlite://")


   # Generator responses can also be inferred. e.g.
   # - A function returning Iterator[T] binds to T
   # - A function returning AsyncIterator[T] binds to T
   @flex.bind
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
       with flex:
           sys.exit(flex.invoke(main))

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

   from flexdi import FlexPack

   flex = FlexPack()


   @flex.bind
   async def provide_engine() -> AsyncIterator[AsyncEngine]:
       engine = create_async_engine("sqlite://")
       try:
           yield engine
       finally:
           await engine.dispose()


   @flex.bind
   async def provide_connection(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
       async with engine.begin() as conn:
           yield conn


   async def main(conn: AsyncConnection) -> int:
       print(await conn.execute(text("SELECT now()")))
       return 0


   if __name__ == "__main__":
       with flex:
           # The injector can handle invoking async functions natively,
           # so no worry about adding in extra logic here.
           sys.exit(flex.invoke(main))
   ...


   # If already within an async context, then you can use the
   # async versions of these methods.
   async def func() -> int:
       async with flex:
           return await flex.ainvoke(main)

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
