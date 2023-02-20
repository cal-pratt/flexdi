[![](https://img.shields.io/pypi/v/flexdi.svg)](https://pypi.org/project/flexdi/)
[![](https://github.com/cal-pratt/flexdi/actions/workflows/main.yml/badge.svg)](https://github.com/cal-pratt/flexdi/actions)

# FlexDI 🚀

`flexdi` is a yet another dependency injection library for Python. `flexdi` provides a lightweight 
alternative to common DI solutions with minimal setup to be included in your projects. This library
is intended for use with type annotated Python libraries, as it leverages these type annotations to 
perform injection.

**Note:** *This repo is still a work in progress and is not yet intended for production use-cases. 
APIs are likely to change in the coming releases*

## Notable features

- __Minimal Setup__<br/>
Some DI systems require that you conform to a particular style of class definition, a naming 
convention to arguments, placing wrappers around class or method definitions, or providing complex 
default arguments which are tied to the DI system. `flexdi` mainly uses type annotations to perform
injection, which avoids a common problem of library lock-in where frameworks force you to design
components using their highly specialized constructs.


- __Inject Any Callable__<br/>
Basic Python DI tools only allow classes to be used for injection, which can be quite limiting.
In `flexdi`, you can provide any typed callable as an input to be invoked. This avoids having to
make class definitions purely for injection to work.


- __Lifetime Management__<br/>
When creating dependencies for your callable, you often have resources that need to be properly 
torn down when your work is done. Providers for types in `flexdi` can be initialized using context 
managers that will have their shutdown logic invoked when you're done your work.


- __Asyncio Support__<br/>
`flexdi` allows calling both sync and async methods directly, and provides both a sync and async 
interface to its main invocation method. Similarly, dependency providers may be defined as async 
methods, or be provided as async context managers.

## High level Overview

`flexdi` offers a construct called the `Injector` which is used to populate callables with
arguments and invoke these callables. These arguments are dependencies you want to inject in your
application.

When determining dependencies for a callable, `flexdi` will examine the type annotations of the
arguments, and construct a graph of objects which can satisfy the callable. A callable can be 
anything from a class (as seen with the type annotations), to functions, class methods, 
generators, etc.

For complex types, `flexdi` allows binding helper functions that can map an instance to a type
definition. These helper functions can themselves be injected with dependencies. Bindings can
also be defined as generators which allows supplying custom teardown logic for your dependencies.

A simple example of an application with SQLAlchemy dependencies:

```py
import sys
from typing import Iterator
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from flexdi import Injector

injector = Injector()

# For simple functions we can infer the type to 
# bind from the return type annotation
@injector.binding()
def provide_engine() -> Engine:
    return create_engine("sqlite://")

# For more complex functions we can explicitly define 
# the type that we bind the result to.
@injector.binding(bind_to=Session)
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
    with injector:
        sys.exit(injector.invoke(main))
```

The same example, but using async code:

```py
import sys
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncConnection, 
    AsyncEngine, 
    create_async_engine
)
from sqlalchemy import text

from flexdi import Injector

injector = Injector()

@injector.binding(bind_to=AsyncEngine)
async def provide_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite://")
    try:
        yield engine
    finally:
        await engine.dispose()

@injector.binding(bind_to=AsyncConnection)
async def provide_connection(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    async with engine.begin() as conn:
        yield conn

async def main(conn: AsyncConnection) -> int:
    print(await conn.execute(text("SELECT now()")))
    return 0

if __name__ == "__main__":
    with injector:
        # The injector can handle invoking async functions natively,
        # so no worry about adding in extra logic here.
        sys.exit(injector.invoke(main))
...

# If already within an async context, then you can use the
# async versions of these methods.
async def func() -> int:
    async with injector:
        return await injector.ainvoke(main)
```


# Why not use an alternative?

Although there are many, many other dependency injection libraries, I found that I was still left 
looking for more lightweight/minimal solutions to this problem. My thoughts on the alternatives:


- [`dependency-injector`](https://github.com/ets-labs/python-dependency-injector) <br/>
This library is probably the most mature out of all the alternatives. Its main driving principal is 
that "Explicit is better than implicit", in that you need to specify explicitly how to assemble/
inject the dependencies. `flexdi` is still explicit in the sense that dependencies are directly 
referenced from their type annotations, and by leveraging them we can avoid a lot of the more 
verbose setup required in `DeclarativeContainer` structures.


- [`fastapi`](https://github.com/tiangolo/fastapi) <br>
This web framework provides an excellent way to perform dependency injection, but it does not
provide a way to perform dependency injection outside the context of web request. When configuring
the injection, you must also provide default values to arguments, which ties application code to the
web framework, making it more difficult to re-use code in other contexts. Additionally, it does not
provide rich support for lifetime/singleton scoped dependencies, making the setup of some 
dependencies increasingly awkward.


- [`pinject`](https://github.com/google/pinject) <br>
This library allows you to perform DI with minimal setup, but its major downfall is that it relies
on the names of arguments to perform injection. If the name of the argument does not match the name
of the class, then you are forced to bind it explicitly. If there are multiple objects that specify
a dependency of a particular type, but use different names, then you need to bind them all
individually as well. And sadly, this project has now been archived and is read-only.

