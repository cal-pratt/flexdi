import asyncio
from typing import Iterator

from flexdi import FlexGraph


# fmt: off
# [Class Definitions: Start]
class Foo:
    pass

class Bar:
    pass
# [Class Definitions: End]

# [Provider Definitions: Start]
def create_foo() -> Iterator[Foo]:
    print("Starting Foo")
    yield Foo()
    print("Ending Foo")

def create_bar() -> Iterator[Bar]:
    print("Starting Bar")
    yield Bar()
    print("Ending Bar")
# [Provider Definitions: End]


# [single_resolve: Start]
async def single_resolve() -> None:
    graph = FlexGraph()

    print("Example Start")

    foo = await graph.resolve(create_foo)

    print("Example End")
# [single_resolve: End]

# [multiple_resolves: Start]
async def multiple_resolves() -> None:
    graph = FlexGraph()

    print("Example Start")

    foo1 = await graph.resolve(create_foo)
    foo2 = await graph.resolve(create_foo)
    print("Foo1 is Foo2:", foo1 is foo2)

    print("Example End")
# [multiple_resolves: End]

# [scope_equivalency_simple: Start]
async def main():
    graph = FlexGraph()

    res = await graph.resolve(create_foo)
# [scope_equivalency_simple: End]

# [scope_equivalency_verbose: Start]
async def main():
    graph = FlexGraph()

    async with graph.application_scope() as app_scope:
        async with app_scope.request_scope() as req_scope:
            res = await req_scope.resolve(create_foo)
# [scope_equivalency_verbose: End]

# [application_scoped_resolve: Start]
async def application_scoped_resolve() -> None:
    graph = FlexGraph()

    graph.bind(create_foo, scope="application")

    print("Before App Scope")
    async with graph.application_scope() as app_scope:
        print("In App Scope")

        foo1 = await app_scope.resolve(create_foo)
        foo2 = await app_scope.resolve(create_foo)
        print("Foo1 is Foo2:", foo1 is foo2)

    print("After App Scope")
# [application_scoped_resolve: End]

# [request_scoped_resolve: Start]
async def request_scoped_resolve() -> None:
    graph = FlexGraph()

    print("Before App Scope")
    async with graph.application_scope() as app_scope:
        print("In App Scope")

        print("Before Req Scope")
        async with app_scope.request_scope() as req_scope:
            print("In Req Scope")

            foo1 = await req_scope.resolve(create_foo)
            foo2 = await req_scope.resolve(create_foo)
            print("Foo1 is Foo2:", foo1 is foo2)

        print("After Req Scope")
    print("After App Scope")
# [request_scoped_resolve: End]

# [eager_dependencies: Start]
async def eager_dependencies() -> None:
    graph = FlexGraph()

    graph.bind(create_foo, scope="application", eager=True)
    graph.bind(create_bar, scope="request", eager=True)

    print("Before App Scope")
    async with graph.application_scope() as app_scope:
        print("In App Scope")

        print("Before Req Scope")
        async with app_scope.request_scope() as req_scope:
            print("In Req Scope")
        print("After Req Scope")

    print("After App Scope")
# [eager_dependencies: End]

# [example5: Start]
async def example5() -> None:
    graph = FlexGraph()

    graph.bind(create_foo)

    print("Before App Scope")
    async with graph.application_scope() as app_scope:
        print("In App Scope")

        print("Before Req Scope")
        async with app_scope.request_scope() as req_scope:
            print("In Req Scope")

            foo1 = await req_scope.resolve(create_foo)
            foo2 = await req_scope.resolve(create_foo)
            print("Foo1 is Foo2:", foo1 is foo2)

        print("After Req Scope")
    print("After App Scope")
# [example5: End]


if __name__ == "__main__":
    print("\nsingle_resolve:\n")
    asyncio.run(single_resolve())

    print("\nmultiple_resolves:\n")
    asyncio.run(multiple_resolves())

    print("\napplication_scoped_resolve:\n")
    asyncio.run(application_scoped_resolve())

    print("\nrequest_scoped_resolve:\n")
    asyncio.run(request_scoped_resolve())

    print("\neager_dependencies:\n")
    asyncio.run(eager_dependencies())

    print("\nExample5:\n")
    asyncio.run(example5())
