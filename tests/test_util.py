from typing import AsyncIterator, Iterator

from flexdi.util import provider_return_type


def test_provider_return_type_standard() -> None:
    def func() -> int:
        return 1

    assert provider_return_type(func) is int


def test_provider_return_type_async() -> None:
    async def func() -> int:
        return 1

    assert provider_return_type(func) is int


def test_provider_return_type_iterator() -> None:
    def func() -> Iterator[int]:
        yield 1

    assert provider_return_type(func) is int


def test_provider_return_type_async_iterator() -> None:
    async def func() -> AsyncIterator[int]:
        yield 1

    assert provider_return_type(func) is int
