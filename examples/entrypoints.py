import asyncio

from flexdi import FlexGraph


# fmt: off
class Foo:
    pass

graph = FlexGraph()

# [entrypoint1: Start]
@graph.entrypoint
def main(foo: Foo) -> None:
    ...
# [entrypoint1: End]

# [entrypoint2: Start]
def _main(foo: Foo) -> None:
    ...

async def _amain() -> None:
    return await graph.resolve(_main)

def main() -> None:
    asyncio.run(_amain())
# [entrypoint2: End]
