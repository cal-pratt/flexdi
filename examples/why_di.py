# fmt: off
# isort: skip_file
# from contextlib import contextmanager
# from typing import Iterator
#
# from sqlalchemy import Engine
#

# [non-injected:start]
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


def main() -> None:
    engine = create_engine("sqlite:///mydb.db")
    try:
        with Session(engine) as session:
            statement = text("SELECT name FROM sqlite_master;")
            for [table_name] in session.execute(statement):
                print(table_name)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
# [non-injected:end]


# [injected-boilerplate:start]
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


def main(session: Session) -> None:
    statement = text("SELECT name FROM sqlite_master;")
    for [table_name] in session.execute(statement):
        print(table_name)


if __name__ == "__main__":
    engine = create_engine("sqlite:///mydb.db")
    try:
        with Session(engine) as session:
            main(session)
    finally:
        engine.dispose()
# [injected-boilerplate:end]


# [injected-nicer:start]
from contextlib import contextmanager
from typing import Iterator
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session


@contextmanager
def provide_engine() -> Iterator[Engine]:
    engine = create_engine("sqlite:///mydb.db")
    try:
        yield engine
    finally:
        engine.dispose()


@contextmanager
def provide_session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def main(session: Session) -> None:
    statement = text("SELECT name FROM sqlite_master;")
    for [table_name] in session.execute(statement):
        print(table_name)


if __name__ == "__main__":
    with provide_engine() as engine:
        with provide_session(engine) as session:
            main(session)
# [injected-nicer:end]

# [injected-interfaces:start]
# provide_engine has no dependencies and can be used to create an Engine
def provide_engine() -> Iterator[Engine]: ...

# provide_session requires an Engine and can be used to create a Session
def provide_session(engine: Engine) -> Iterator[Session]: ...

# main requires a Session and can then be called.
def main(session: Session) -> None: ...
# [injected-interfaces:end]

# [injected-connections:start]
with provide_engine() as engine:
    with provide_session(engine) as session:
        main(session)
# [injected-connections:end]
