from typing import Any, AsyncGenerator, AsyncIterator, Generator, Iterator

import pytest

# Import of Annotated not available from typing until 3.9
from typing_extensions import Annotated

from flexdi._util import determine_return_type
from flexdi.errors import UntypedError


class SimpleClass:
    pass


def sync_func() -> int:
    return 1


async def async_func() -> int:
    return 1


def sync_iter() -> Iterator[int]:
    yield 1


async def async_iter() -> AsyncIterator[int]:
    yield 1


def sync_generator() -> Generator[int, Any, Any]:
    yield 1


async def async_generator() -> AsyncGenerator[int, Any]:
    yield 1


@pytest.mark.parametrize(
    "test_input,expected_output",
    [
        pytest.param(SimpleClass, SimpleClass, id="SimpleClass"),
        pytest.param(sync_func, int, id="SyncFunction"),
        pytest.param(async_func, int, id="AsyncFunction"),
        pytest.param(sync_iter, int, id="SyncIterator"),
        pytest.param(async_func, int, id="AsyncIterator"),
        pytest.param(sync_generator, int, id="SyncGenerator"),
        pytest.param(async_generator, int, id="AsyncGenerator"),
    ],
)
def test_determine_return_type(test_input: Any, expected_output: Any) -> None:
    actual_output = determine_return_type(test_input)
    assert actual_output is expected_output


def invalid_typed_func():  # type: ignore
    return 1


@pytest.mark.parametrize(
    "test_input",
    [
        pytest.param(Annotated[int, "i"], id="NonInstantiableClass"),
        pytest.param(invalid_typed_func, id="MissingReturnStatement"),
    ],
)
def test_determine_invalid_return_type(test_input: Any) -> None:
    with pytest.raises(UntypedError):
        determine_return_type(invalid_typed_func)
