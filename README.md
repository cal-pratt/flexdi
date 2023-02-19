[![](https://github.com/cal-pratt/flexdi/actions/workflows/main.yml/badge.svg)](https://github.com/cal-pratt/flexdi/actions)

# FlexDI 🚀

`flexdi` is a yet another dependency injection library for Python.
`flexdi` provides a lightweight alternative to common DI solutions
with minimal setup to be included in your projects. This library
is intended for use with type annotated Python libraries, as it
leverages these type annotations to perform injection.

**Note:** *This repo is still a work in progress and is not yet intended
for production use-cases.*

## Notable features

- __Minimal Setup__<br/>
Some DI systems require that you conform to a particular style of class
definition, a naming convention to arguments, placing wrappers around class
or method definitions, or providing complex default arguments which are
tied to the DI system.
`flexdi` mainly uses type annotations to perform injection, which avoids
the library lock-in, and allows your components to remain as re-usable as 
possible.
    ```py
    from flexdi import Injector
    injector = Injector()
    
    class Foo:
        pass
    
    def main(foo: Foo) -> int:
        return 0
    
    if __name__ == "__main__":
        sys.exit(injector.invoke(main))
    ```

- __Inject Any Callable__<br/>
Most Python DI tools rely on classes to always be used for injection.
In `flexdi`, you can provide any typed callable as an input to be invoked.
This avoids having to make class definitions purely for injection to work.
    ```py
    class Foo:
        pass

    def bar(foo: Foo) -> Foo:
        return foo
    
    foo = injector.invoke(Foo)  # Construct a class:
    foo = injector.invoke(bar)  # Call a method
    ```

- __Lifetime Management__<br/>
When creating dependencies for your callable, you often have resources
that need to be properly torn down when your work is done. Providers for
types in `flexdi` can be initialized using context managers that will have
their shutdown logic invoked when you're done your work.
    ```py
    class QueryClient:
        def __init__(self, db: Database) -> None:
            self.db = db
  
        def query(self, name: str) -> str:
            ...

    # We can also use bindings to map class names!
    @injector.binding(bind_to=Database)
    def provider() -> Iterator[MySQLDatabase]:
        database = MySQLDatabase(...)
        try:
            yield database
        finally:
            database.close()

    with injector:
        query_client = injector.invoke(query)
        res = query_client.query("alice")
    ```

- __Asyncio Support__<br/>
    `flexdi` allows calling both sync and async methods directly, and provides both 
    a sync and async interface to its main invocation method. 
    Similarly, dependency providers may be defined as async methods, or be provided
    as async context managers.
    ```py
    async def query(db: Database) -> str:
        return await db.query()
  
    async def main() -> int:
        async with Injector() as injector:
            # bindings can infer a mapping from the return type
            @injector.binding()
            async def provider() -> Database:
                db = await ...
                return db
    
            res = await injector.ainvoke(query)
    ```

# Why not use an alternative?

Although there are many, many other dependency injection libraries, I found that I was
still left looking for more lightweight/minimal solutions to this problem. My thoughts 
on the alternatives:


- [`dependency-injector`](https://github.com/ets-labs/python-dependency-injector) <br/>
    This library is probably the most mature out of all the alternatives. Its main
    driving principal is that "Explicit is better than implicit", in that you need
    to specify explicitly how to assemble/inject the dependencies.
    `flexdi` is still explicit in the sense that dependencies are directly referenced
    from their type annotations, and by leveraging them we can avoid a lot of the more
    verbose setup required in `DeclarativeContainer` structures.


- [`fastapi`](https://github.com/tiangolo/fastapi) <br>
    This web framework provides an excellent way to perform dependency injection,
    but it does not provide a way to perform dependency injection outside the 
    context of web request. When configuring the injection, you must also provide
    default values to arguments, which ties application code to the web framework,
    making it more difficult to re-use code in other contexts. Additionally, it does
    not provide rich support for lifetime/singleton scoped dependencies, making the 
    setup of some dependencies increasingly awkward.


- [`pinject`](https://github.com/google/pinject) <br>
    This library allows you to perform DI with minimal setup, but its major
    downfall is that it relies on the names of arguments to perform injection.
    If the name of the argument does not match the name of the class, then you are
    forced to bind it explicitly.
    If there are multiple objects that specify a dependency of a particular type,
    but use different names, then you need to bind them all individually as well.
    And sadly, this project has now been archived and is read-only.

