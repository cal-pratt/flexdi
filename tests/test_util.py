from typing import AsyncIterator, Iterator

# Import of Annotated not available from typing until 3.9
from typing_extensions import Annotated

from flexdi.util import determine_return_type


def test_determine_return_type_annotated() -> None:
    assert determine_return_type(Annotated[int, "value1"]) is Annotated[int, "value1"]


def test_determine_return_type_standard() -> None:
    def func() -> int:
        return 1

    assert determine_return_type(func) is int


def test_determine_return_type_async() -> None:
    async def func() -> int:
        return 1

    assert determine_return_type(func) is int


def test_determine_return_type_iterator() -> None:
    def func() -> Iterator[int]:
        yield 1

    assert determine_return_type(func) is int


def test_determine_return_type_async_iterator() -> None:
    async def func() -> AsyncIterator[int]:
        yield 1

    assert determine_return_type(func) is int
