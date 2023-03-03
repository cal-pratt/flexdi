from typing import AsyncIterator, Iterator

from fastapi import FastAPI
from starlette.testclient import TestClient

from flexdi.fastapi import FastAPIGraph, FlexDepends


def test_fastapi_scopes_sync() -> None:
    app = FastAPI()
    graph = FastAPIGraph(app)

    class SingletonDependency:
        pass

    class RequestDependency:
        pass

    events = []

    @graph.bind(scope="application", eager=True)
    def singleton_dependency() -> Iterator[SingletonDependency]:
        events.append("singleton-start")
        yield SingletonDependency()
        events.append("singleton-end")

    @graph.bind
    def request_dependency() -> Iterator[RequestDependency]:
        events.append("request-start")
        yield RequestDependency()
        events.append("request-end")

    @app.get("/")
    def test_endpoint(
        singleton_dep: SingletonDependency = FlexDepends(SingletonDependency),
        request_dep: RequestDependency = FlexDepends(RequestDependency),
    ) -> None:
        pass

    assert events == []
    with TestClient(app) as client:
        assert events == [
            "singleton-start",
        ]
        assert client.get("/").status_code == 200
        assert events == [
            "singleton-start",
            "request-start",
            "request-end",
        ]
        assert client.get("/").status_code == 200
        assert events == [
            "singleton-start",
            "request-start",
            "request-end",
            "request-start",
            "request-end",
        ]
    assert events == [
        "singleton-start",
        "request-start",
        "request-end",
        "request-start",
        "request-end",
        "singleton-end",
    ]


def test_fastapi_scopes_async() -> None:
    app = FastAPI()
    graph = FastAPIGraph(app)

    class SingletonDependency:
        pass

    class RequestDependency:
        pass

    events = []

    @graph.bind(scope="application")
    async def singleton_dependency() -> AsyncIterator[SingletonDependency]:
        events.append("singleton-start")
        yield SingletonDependency()
        events.append("singleton-end")

    @graph.bind
    async def request_dependency() -> AsyncIterator[RequestDependency]:
        events.append("request-start")
        yield RequestDependency()
        events.append("request-end")

    @app.get("/")
    async def test_endpoint(
        singleton_dep: SingletonDependency = FlexDepends(SingletonDependency),
        request_dep: RequestDependency = FlexDepends(RequestDependency),
    ) -> None:
        pass

    assert events == []
    with TestClient(app) as client:
        assert events == []
        client.get("/")
        assert events == [
            "singleton-start",
            "request-start",
            "request-end",
        ]
        client.get("/")
        assert events == [
            "singleton-start",
            "request-start",
            "request-end",
            "request-start",
            "request-end",
        ]
    assert events == [
        "singleton-start",
        "request-start",
        "request-end",
        "request-start",
        "request-end",
        "singleton-end",
    ]
