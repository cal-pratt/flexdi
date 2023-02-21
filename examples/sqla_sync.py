import sys
from typing import Iterator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from flexdi import FlexGraph

# The FlexGraph keeps track of what dependencies different
# providers require, and will later be used to resolve them.
graph = FlexGraph()


# Let's add a binding for an Engine. Anything that requires an Engine will
# now fetch it from provide_engine.
# FlexGraph uses the functions return type annotation to perform the binding.
@graph.bind
def provide_engine() -> Engine:
    return create_engine("sqlite://")


# Generator responses can also be used. e.g.
# - A function returning Iterator[T] binds to T
# - A function returning AsyncIterator[T] binds to T
@graph.bind
def provide_session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def execute(session: Session) -> int:
    print(session.execute(text("SELECT datetime('now');")).one())
    return 0


# We always call the graph from a with statement to ensure
# we clean up any dependencies which require teardown
def main() -> int:
    with graph:
        return graph.resolve(main)


if __name__ == "__main__":
    sys.exit(main())
