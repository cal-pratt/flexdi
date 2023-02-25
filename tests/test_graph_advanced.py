import pytest

from flexdi import FlexGraph


@pytest.mark.asyncio
async def test_flexgraph_dependency() -> None:
    """
    For some cases, you might want a dependency to have an instance of the
    graph itself. Each instance of the graph should have a special binding
    which adds its own instance as a dependency that can be resolved.
    """

    async with FlexGraph() as original:
        resolved = await original.resolve(FlexGraph)

    assert resolved is original


@pytest.mark.asyncio
async def test_flexgraph_chained_dependency() -> None:
    """
    If we chain the dependency graph, then we will the FlexGraph to be updated
    now use the chained instance if requested.
    """

    async with FlexGraph() as original:
        async with original.chain() as chained:
            resolved = await chained.resolve(FlexGraph)

    assert resolved is chained
    assert resolved is not original


@pytest.mark.asyncio
async def test_flexgraph_override_dependency() -> None:
    """
    If we override the dependency graph, then we expect that there is still only
    one instance of the flexgraph, because all we do is protect the state.
    """

    original = FlexGraph()
    with original.override():
        async with original:
            resolved = await original.resolve(FlexGraph)

    assert resolved is original
