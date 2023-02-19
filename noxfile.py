import nox

PYTHON_VERSION = "3.11"
BLACK_ARGS = ["black", "src/", "tests/"]
ISORT_ARGS = ["isort", "src/", "tests/"]
DEV_DEPS = [
    "black >= 23.1.0",
    "bumpversion >= 0.6.0",
    "flake8 >= 6.0.0",
    "isort >= 5.12.0",
    "mypy >= 1.0.1",
    "pydantic >= 1.10.5",
    "pytest >= 7.2.1",
    "pytest-asyncio >= 0.20.3",
]

nox.options.sessions = ["dev"]


@nox.session(python=PYTHON_VERSION, reuse_venv=True)
def dev(session):
    session.install("nox")
    session.install(*DEV_DEPS)
    session.install("-e", ".")


@nox.session(python=PYTHON_VERSION)
def tests(session):
    session.install(*DEV_DEPS)
    session.install("-e", ".")
    session.run("pytest", "tests/")


@nox.session(python=PYTHON_VERSION)
def clean(session):
    session.install(*DEV_DEPS)
    session.install("-e", ".")
    session.run(*BLACK_ARGS)
    session.run(*ISORT_ARGS)


@nox.session(python=PYTHON_VERSION)
def flake8(session):
    session.install(*DEV_DEPS)
    session.install("-e", ".")
    session.run("flake8", "--version")
    session.run("flake8", "src/", "tests/")


@nox.session(python=PYTHON_VERSION)
def black(session):
    session.install(*DEV_DEPS)
    session.install("-e", ".")
    session.run("black", "--version")
    session.run(*BLACK_ARGS, "--check", "--diff")


@nox.session(python=PYTHON_VERSION)
def isort(session):
    session.install(*DEV_DEPS)
    session.install("-e", ".")
    session.run(*ISORT_ARGS, "--diff", "--check-only")


@nox.session(python=PYTHON_VERSION)
def mypy(session):
    session.install(*DEV_DEPS)
    session.install("-e", ".")
    session.run("mypy", "--strict", "src/", "tests/")


@nox.session(python=PYTHON_VERSION)
def publish(session):
    session.install("twine >= 4.0.2", "build >= 0.10.0")
    session.run("python", "-m", "build")
    session.run("twine", "upload", "dist/*")


@nox.session(python=PYTHON_VERSION)
def test_publish(session):
    session.install("twine >= 4.0.2", "build >= 0.10.0")
    session.run("python", "-m", "build")
    session.run("twine", "upload", "-r", "testpypi", "dist/*")
