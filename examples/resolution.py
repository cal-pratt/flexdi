import asyncio
from typing import Iterator

from flexdi import FlexGraph


# fmt: off
# [Class Definitions: Start]
class Foo: pass
class Bar: pass
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


# [example1: Start]
async def example1() -> None:
    graph = FlexGraph()

    async with graph:
        foo = await graph.resolve(create_foo)
# [example1: End]

# [example2: Start]
async def example2() -> None:
    graph = FlexGraph()

    async with graph:
        foo1 = await graph.resolve(create_foo)
        foo2 = await graph.resolve(create_foo)
        print("Foo1 is Foo2:", foo1 is foo2)
# [example2: End]

# [example3: Start]
async def example3() -> None:
    graph = FlexGraph()

    graph.bind(create_foo, eager=True)
    graph.bind(create_bar)

    async with graph:
        print("Inside the with block")
# [example3: End]

# [example4: Start]
async def example4() -> None:
    parent = FlexGraph()

    parent.bind(create_foo, eager=True)
    parent.bind(create_bar)

    async with parent:
        print("Parent Block")

        async with parent.chain() as child:
            print("Child Block")
            await child.resolve(Bar)
            # Notice that Foo is not recreated!
            await child.resolve(Foo)

        async with parent.chain() as child:
            print("Child Block")
            await child.resolve(Bar)
# [example4: End]


if __name__ == "__main__":
    print("\nExample1:\n")
    asyncio.run(example1())

    print("\nExample2:\n")
    asyncio.run(example2())

    print("\nExample3:\n")
    asyncio.run(example3())

    print("\nExample4:\n")
    asyncio.run(example4())
