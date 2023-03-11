import sys
from typing import Iterator

import pytest
from flask.testing import FlaskClient

from .test_app import app_flask


@pytest.fixture
def graph() -> Iterator[None]:
    with app_flask.graph.override():
        yield


@pytest.fixture(autouse=True)
def mock_client() -> Iterator[FlaskClient]:
    yield app_flask.app.test_client()


def test_sync_endpoint_different_threads(mock_client: FlaskClient) -> None:
    assert (data := mock_client.get("/sync").json)
    singleton_thread, request_thread = data
    assert singleton_thread != request_thread


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason=(
        "This seems to run on a separate thread when using windows. "
        "It's unclear whats causing this behavior, but GitHub actions "
        "running on ubuntu has the desired behavior."
    ),
)
def test_async_endpoint_same_threads(mock_client: FlaskClient) -> None:
    assert (data := mock_client.get("/async").json)
    singleton_thread, request_thread = data
    assert singleton_thread == request_thread
