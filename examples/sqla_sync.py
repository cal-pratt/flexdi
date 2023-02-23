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


# An entrypoint is a convenience method for creating no argument
# version of a function or coroutine. You should typically only
# have one entry point used in your applications.
@graph.entrypoint
def main(session: Session) -> int:
    print(session.execute(text("SELECT datetime('now');")).one())
    return 0


# Notice that we call main with no arguments!
if __name__ == "__main__":
    sys.exit(main())
