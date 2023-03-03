from typing import Iterator

import pytest
from _pytest.capture import CaptureFixture
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from .sqla_sync import graph, main


# This simple fixture allows overrides to bindings on the graph.
# The overrides will be removed after each test case is completed.
# Each test case can choose to bind different mocks to suit its needs.
@pytest.fixture(autouse=True)
def graph_override() -> Iterator[None]:
    with graph.override():
        yield


# Use an in-memory db for tests, and override the real binding
@pytest.fixture(autouse=True)
def engine() -> Engine:
    engine = create_engine("sqlite://")
    graph.bind_instance(engine)
    return engine


def test_reading_tables(engine: Engine, capsys: CaptureFixture[str]) -> None:
    statement = text("CREATE TABLE foobar (id);")
    with Session(engine) as session:
        session.execute(statement)

    main()
    assert capsys.readouterr().out == "foobar\n"
