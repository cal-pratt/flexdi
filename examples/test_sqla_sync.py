from typing import Iterator

import pytest
from _pytest.capture import CaptureFixture
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from .sqla_sync import graph, main


# This simple fixture allows overriden bindings on the graph
# and have them removed after each test is completed.
# This allows test-cases to easily bind different mocks per test.
@pytest.fixture(autouse=True)
def graph_override() -> Iterator[None]:
    with graph.override():
        yield


# For this test we'll use an in-memory db
@pytest.fixture(autouse=True)
def engine() -> Engine:
    engine = create_engine("sqlite://")
    # For an instance, the type can be inferred from calling type()
    graph.bind_instance(engine)
    return engine


def test_reading_tables(engine: Engine, capsys: CaptureFixture[str]) -> None:
    statement = text("CREATE TABLE foobar (id);")
    with Session(engine) as session:
        session.execute(statement)

    main()
    assert capsys.readouterr().out == "foobar\n"
