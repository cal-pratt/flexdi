import webbrowser

import nox
import os
import shutil

PYTHON_VERSION = "3.11"
SUPPORTED_VERSIONS = ["3.8", "3.9", "3.10", "3.11"]
BLACK_ARGS = ["black", "src/", "tests/", "examples/"]
ISORT_ARGS = ["isort", "src/", "tests/", "examples/"]
LOCAL_PACKAGE = ".[grpc]"
DEV_DEPS = [
    "black >= 23.1.0",
    "bumpversion >= 0.6.0",
    "fastapi >= 0.92.0",
    "flake8 >= 6.0.0",
    "Flask[async] >= 2.2.3",
    "grpcio-tools >= 1.53.0",
    "grpc-stubs >= 1.53",
    "httpx >= 0.23.3",
    "isort >= 5.12.0",
    "mypy >= 1.0.1",
    "mypy-protobuf >= 3.4.0",
    "pydantic >= 1.10.5",
    "pytest >= 7.2.1",
    "pytest-asyncio >= 0.20.3",
]

nox.options.sessions = ["dev"]


@nox.session(python=PYTHON_VERSION, reuse_venv=True)
def dev(session):
    session.install("nox")
    session.install(*DEV_DEPS)
    session.install("-e", LOCAL_PACKAGE)


@nox.session(python=SUPPORTED_VERSIONS, reuse_venv=True)
def tests(session):
    session.install(*DEV_DEPS)
    session.install("-e", LOCAL_PACKAGE)
    session.run("pytest", "tests/")


@nox.session(python=PYTHON_VERSION, reuse_venv=True)
def clean(session):
    session.install(*DEV_DEPS)
    session.install("-e", LOCAL_PACKAGE)
    session.run(*BLACK_ARGS)
    session.run(*ISORT_ARGS)


@nox.session(python=PYTHON_VERSION, reuse_venv=True)
def flake8(session):
    session.install(*DEV_DEPS)
    session.install("-e", LOCAL_PACKAGE)
    session.run("flake8", "--version")
    session.run("flake8", "src/", "tests/")


@nox.session(python=PYTHON_VERSION, reuse_venv=True)
def black(session):
    session.install(*DEV_DEPS)
    session.install("-e", LOCAL_PACKAGE)
    session.run("black", "--version")
    session.run(*BLACK_ARGS, "--check", "--diff")


@nox.session(python=PYTHON_VERSION, reuse_venv=True)
def isort(session):
    session.install(*DEV_DEPS)
    session.install("-e", LOCAL_PACKAGE)
    session.run(*ISORT_ARGS, "--diff", "--check-only")


@nox.session(python=PYTHON_VERSION, reuse_venv=True)
def mypy(session):
    session.install(*DEV_DEPS)
    session.install("-e", LOCAL_PACKAGE)
    session.run("mypy", "--strict", "--python-version", "3.8", "src/", "tests/")


@nox.session(python=PYTHON_VERSION, reuse_venv=True)
def protos(session):
    session.install(*DEV_DEPS)
    session.install("-e", LOCAL_PACKAGE)
    session.run(
        "python",
        "-m",
        "grpc_tools.protoc",
        "-Itests/test_app/protos",
        "--python_out=tests/test_app/protos",
        "--grpc_python_out=tests/test_app/protos",
        "--proto_path=tests/test_app/protos",
        "--mypy_out=tests/test_app/protos",
        "--mypy_grpc_out=tests/test_app/protos",
        "tests/test_app/protos/hello.proto",
    )

    replacements = {
        "tests/test_app/protos/hello_pb2_grpc.py": [
            ["import hello_pb2 as hello__pb2", "from . import hello_pb2 as hello__pb2"]
        ],
        "tests/test_app/protos/hello_pb2_grpc.pyi": [
            ["import hello_pb2", "from . import hello_pb2 as hello_pb2"],
            ["import grpc", "import grpc.aio as grpc\nimport typing"],
            ["context: grpc.ServicerContext,", "context: grpc.ServicerContext[typing.Any, typing.Any],"]
        ],
    }

    for filename, changes in replacements.items():
        with open(filename, "r") as f:
            contents = f.read()
            for orig, update in changes:
                contents = contents.replace(orig, update)
        with open(filename, "w") as f:
            f.write(contents)


@nox.session(python=PYTHON_VERSION)
def publish(session):
    session.install("twine >= 4.0.2", "build >= 0.10.0")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    session.run("python", "-m", "build")
    session.run("twine", "upload", "dist/*")


@nox.session(python=PYTHON_VERSION)
def test_publish(session):
    session.install("twine >= 4.0.2", "build >= 0.10.0")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    session.run("python", "-m", "build")
    session.run("twine", "upload", "-r", "testpypi", "dist/*")


@nox.session(python=PYTHON_VERSION, reuse_venv=True)
def docs(session):
    session.install("Sphinx >= 6.1.3", "sphinx-rtd-theme >= 1.2.0")
    session.install("-e", LOCAL_PACKAGE)
    if os.path.exists("docs/build"):
        shutil.rmtree("docs/build")
    session.run("sphinx-build", "-a", "docs/source", "docs/build")

    # regenerate the README.rst
    with open("README.rst", "w") as readme_file:
        readme_file.write(gen_readme())

    print(f'file:///{os.path.abspath("docs/build/index.html")}')


def gen_readme() -> str:
    def readall(file_name: str) -> str:
        with open(file_name, "r") as file:
            return file.read()

    def readall_indent(file_name: str) -> str:
        lines = readall(file_name).split("\n")
        return "\n".join(f"    {line}" for line in lines)

    return f"""
{readall("docs/source/header.rst")}

|
| The full documentation is available at `flexdi.readthedocs.io <https://flexdi.readthedocs.io>`_.

{readall("docs/source/goals.rst")}

Overview
========

{readall("docs/source/overview.rst")}

Example Usage
-------------

A simple example of an application with SQLAlchemy dependencies:

.. code:: python

{readall_indent("examples/sqla_sync.py")}

The same example, but using async code:

.. code:: python

{readall_indent("examples/sqla_async.py")}

{readall("docs/source/alternatives.rst")}

Want to make a contribution?
----------------------------

See `CONTRIBUTING.md <https://github.com/cal-pratt/flexdi/blob/main/CONTRIBUTING.md>`_
"""
