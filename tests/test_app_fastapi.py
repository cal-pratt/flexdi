from typing import Iterator

import pytest
from starlette.testclient import TestClient

from .test_app import app_fastapi


@pytest.fixture
def graph() -> Iterator[None]:
    with app_fastapi.graph.override():
        yield


@pytest.fixture(autouse=True)
def mock_client() -> Iterator[TestClient]:
    with TestClient(app_fastapi.app) as client:
        yield client


def test_sync_endpoint_different_threads(mock_client: TestClient) -> None:
    singleton_thread, request_thread = mock_client.get("/sync").json()
    assert singleton_thread != request_thread


def test_async_endpoint_same_threads(mock_client: TestClient) -> None:
    singleton_thread, request_thread = mock_client.get("/async").json()
    assert singleton_thread == request_thread
