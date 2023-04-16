from typing import Iterator

import pytest
from _pytest.capture import CaptureFixture

from flexdi import FlexGraph

from .test_app import app_cli


class MockClient:
    def foo(self) -> str:
        return "bar"


@pytest.fixture
def graph() -> Iterator[FlexGraph]:
    with app_cli.graph.override():
        yield app_cli.graph


@pytest.fixture
def mock_client(graph: FlexGraph) -> MockClient:
    return graph.bind_instance(MockClient(), resolves=app_cli.ApiClient)


def test_main_normal(capsys: CaptureFixture[str]) -> None:
    app_cli.main()
    assert capsys.readouterr().out == "foo\n"


def test_main_override(mock_client: MockClient, capsys: CaptureFixture[str]) -> None:
    app_cli.main()
    assert capsys.readouterr().out == "bar\n"


def test_main_again(capsys: CaptureFixture[str]) -> None:
    app_cli.main()
    assert capsys.readouterr().out == "foo\n"


@pytest.mark.asyncio
async def test_main_again_async(capsys: CaptureFixture[str]) -> None:
    await app_cli.main.aio()
    assert capsys.readouterr().out == "foo\n"
