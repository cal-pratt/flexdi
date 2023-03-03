from typing import Iterator

import pytest

from flexdi import FlexGraph


@pytest.mark.asyncio
async def test_request_scope_startup() -> None:
    events = []

    def foo() -> Iterator[int]:
        events.append("start")
        yield 1
        events.append("end")

    graph = FlexGraph()

    await graph.resolve(foo)
    await graph.resolve(foo)

    assert events == ["start", "end", "start", "end"]
    events.clear()

    async with graph.application_scope() as app_scope:
        await app_scope.resolve(foo)
        await app_scope.resolve(foo)

    assert events == ["start", "end", "start", "end"]
    events.clear()

    async with graph.application_scope() as app_scope:
        async with app_scope.request_scope() as req_scope:
            await req_scope.resolve(foo)
            await req_scope.resolve(foo)

    assert events == ["start", "end"]
    events.clear()


@pytest.mark.asyncio
async def test_application_scope_startup() -> None:
    events = []

    def foo() -> Iterator[int]:
        events.append("start")
        yield 1
        events.append("end")

    graph = FlexGraph()
    graph.bind(foo, scope="application")

    await graph.resolve(foo)
    await graph.resolve(foo)

    assert events == ["start", "end", "start", "end"]
    events.clear()

    async with graph.application_scope() as app_scope:
        await app_scope.resolve(foo)
        await app_scope.resolve(foo)

    assert events == ["start", "end"]
    events.clear()

    async with graph.application_scope() as app_scope:
        async with app_scope.request_scope() as req_scope:
            await req_scope.resolve(foo)
            await req_scope.resolve(foo)
        await req_scope.resolve(foo)
        await req_scope.resolve(foo)

    assert events == ["start", "end"]
    events.clear()
