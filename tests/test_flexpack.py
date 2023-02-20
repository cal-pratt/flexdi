from dataclasses import dataclass
from typing import Any, AsyncIterator, Iterator

import pytest
from pydantic import BaseModel

# Import of Annotated not available from typing until 3.9
# Import of assert_type not available from typing until 3.11
from typing_extensions import Annotated, assert_type

from flexdi import CycleError, FlexPack


def test_dependant_simple() -> None:
    """
    For a simple class with no arguments, we should be able to easily determine
    the dependency tree.
    """

    class Foo:
        pass

    with FlexPack() as flex:
        res = flex.invoke(Foo)
        assert isinstance(res, Foo)


def test_dependant_chained() -> None:
    """
    When arguments are specified, follow the tree to construct them.
    """

    class Foo:
        pass

    class Bar:
        def __init__(self, dep1: Foo) -> None:
            self.dep1 = dep1

    with FlexPack() as flex:
        res = flex.invoke(Bar)
        assert isinstance(res, Bar)
        assert isinstance(res.dep1, Foo)


def test_dependant_chained_dataclasses() -> None:
    """
    Now lets try it with dataclasses.
    """

    @dataclass
    class Foo:
        pass

    @dataclass
    class Bar:
        dep1: Foo

    with FlexPack() as flex:
        res = flex.invoke(Bar)
        assert isinstance(res, Bar)
        assert isinstance(res.dep1, Foo)


def test_dependant_chained_pydantic() -> None:
    """
    Now lets try it with pydantic models used.
    """

    class Foo(BaseModel):
        pass

    class Bar(BaseModel):
        dep1: Foo

    with FlexPack() as flex:
        res = flex.invoke(Bar)
        assert isinstance(res, Bar)
        assert isinstance(res.dep1, Foo)


def test_cycle_detection() -> None:
    """
    This is a bit of a contrived case, but if there are cycles present in the
    dependency tree, we should fail as there would be no way to construct the
    object required.
    """

    class Foo:
        pass

    class Bar:
        pass

    def foo_init(self: Foo, dep1: Bar) -> None:
        self.dep1 = dep1  # type: ignore

    def bar_init(self: Bar, dep1: Foo) -> None:
        self.dep1 = dep1  # type: ignore

    Foo.__init__ = foo_init  # type: ignore
    Bar.__init__ = bar_init  # type: ignore

    with FlexPack() as flex:
        with pytest.raises(CycleError):
            flex.invoke(Foo)
        with pytest.raises(CycleError):
            flex.invoke(Bar)


def test_provider() -> None:
    @dataclass
    class Foo:
        value: int

    @dataclass
    class Bar:
        dep1: Foo

    flex = FlexPack()

    @flex.bind
    def foo_provider() -> Foo:
        return Foo(2)

    with flex:
        res = flex.invoke(Bar)
        assert isinstance(res, Bar)
        assert isinstance(res.dep1, Foo)
        assert res.dep1.value == 2


def test_provider_no_decorator() -> None:
    @dataclass
    class Foo:
        value: int

    @dataclass
    class Bar:
        dep1: Foo

    def foo_provider() -> Foo:
        return Foo(2)

    flex = FlexPack()
    flex.bind(foo_provider)

    with flex:
        res = flex.invoke(Bar)
        assert isinstance(res, Bar)
        assert isinstance(res.dep1, Foo)
        assert res.dep1.value == 2


def test_provider_lambda() -> None:
    @dataclass
    class Foo:
        value: int

    @dataclass
    class Bar:
        dep1: Foo

    flex = FlexPack()
    flex.bind(lambda: Foo(2), target=Foo)

    with flex:
        res = flex.invoke(Bar)
        assert isinstance(res, Bar)
        assert isinstance(res.dep1, Foo)
        assert res.dep1.value == 2


def test_provider_interface_map() -> None:
    @dataclass
    class Foo:
        pass

    @dataclass
    class FooChild(Foo):
        pass

    @dataclass
    class Bar:
        dep1: Foo

    flex = FlexPack()
    flex.bind(FooChild, target=Foo)

    with flex:
        res = flex.invoke(Bar)
        assert isinstance(res, Bar)
        assert isinstance(res.dep1, FooChild)


def test_provider_lower_level() -> None:
    @dataclass
    class Foo:
        value: int

    @dataclass
    class Bar:
        dep1: Foo

    flex = FlexPack()

    @flex.bind
    def value_provider() -> int:
        return 2

    with flex:
        res = flex.invoke(Bar)
        assert isinstance(res, Bar)
        assert isinstance(res.dep1, Foo)
        assert res.dep1.value == 2


def test_provider_clazz_mapping() -> None:
    @dataclass
    class Foo:
        value: int

    flex = FlexPack()

    @flex.bind(target=int)
    def value_provider() -> Any:
        return 3

    with flex:
        res = flex.invoke(Foo)
        assert isinstance(res, Foo)
        assert res.value == 3


def test_provider_annotated() -> None:
    @dataclass
    class Foo:
        value1: Annotated[int, "value1"]
        value2: Annotated[int, "value2"]

    flex = FlexPack()

    @flex.bind
    def value1_provider() -> Annotated[int, "value1"]:
        return 123

    @flex.bind
    def value2_provider() -> Annotated[int, "value2"]:
        return 456

    with flex:
        res = flex.invoke(Foo)
        assert isinstance(res, Foo)
        assert res.value1 == 123
        assert res.value2 == 456


def test_provider_annotated_mapping() -> None:
    @dataclass
    class Foo:
        value1: Annotated[int, "value1"]
        value2: Annotated[int, "value2"]

    flex = FlexPack()

    @flex.bind(target=Annotated[int, "value1"])
    def value1_provider() -> int:
        return 123

    @flex.bind(target=Annotated[int, "value2"])
    def value2_provider() -> int:
        return 456

    with flex:
        res = flex.invoke(Foo)
        assert isinstance(res, Foo)
        assert res.value1 == 123
        assert res.value2 == 456


def test_provider_annotated_chained() -> None:
    @dataclass
    class Foo:
        value1: Annotated[int, "value1"]
        value2: Annotated[int, "value2"]

    flex = FlexPack()

    @flex.bind
    def value1_provider() -> Annotated[int, "value1"]:
        return 123

    @flex.bind(target=Annotated[int, "value2"])
    def value2_provider(value1: Annotated[int, "value1"]) -> int:
        return value1 + 111

    with flex:
        res = flex.invoke(Foo)
        assert isinstance(res, Foo)
        assert res.value1 == 123
        assert res.value2 == 234


def test_singleton() -> None:
    @dataclass
    class Foo:
        value1: int
        value2: str

    flex = FlexPack()

    called_value1_provider = 0
    called_value2_provider = 0

    @flex.bind(eager=True)
    def value1_provider() -> int:
        nonlocal called_value1_provider
        called_value1_provider += 1
        return 1

    @flex.bind
    def value2_provider() -> str:
        nonlocal called_value2_provider
        called_value2_provider += 1
        return "2"

    with flex:
        with flex.chain() as sub_injector:
            sub_injector.invoke(Foo)
        with flex.chain() as sub_injector:
            sub_injector.invoke(Foo)

    assert called_value1_provider == 1
    assert called_value2_provider == 2

    with flex:
        with flex.chain() as sub_injector:
            sub_injector.invoke(Foo)
        with flex.chain() as sub_injector:
            sub_injector.invoke(Foo)

    assert called_value1_provider == 2
    assert called_value2_provider == 4


def test_sync_dep_provider() -> None:
    @dataclass
    class Foo:
        value: int

    flex = FlexPack()

    provider_events = []

    @flex.bind
    def provider() -> int:
        provider_events.append("entered")
        return 1

    with flex:
        provider_events = []

        res = flex.invoke(Foo)
        assert isinstance(res, Foo)
        assert res.value == 1

        provider_events = ["entered"]

    provider_events = ["entered"]


def test_async_dep_provider() -> None:
    @dataclass
    class Foo:
        value: int

    flex = FlexPack()

    provider_events = []

    @flex.bind
    async def provider() -> int:
        provider_events.append("entered")
        return 1

    with flex:
        provider_events = []

        res = flex.invoke(Foo)
        assert isinstance(res, Foo)
        assert res.value == 1

        provider_events = ["entered"]

    provider_events = ["entered"]


def test_sync_gen_provider() -> None:
    @dataclass
    class Foo:
        value: int

    flex = FlexPack()

    provider_events = []

    @flex.bind
    def provider() -> Iterator[int]:
        provider_events.append("entered")
        try:
            yield 1
        finally:
            provider_events.append("exited")

    with flex:
        provider_events = []

        res = flex.invoke(Foo)
        assert isinstance(res, Foo)
        assert res.value == 1

        provider_events = ["entered"]

    provider_events = ["entered", "exited"]


def test_async_gen_provider() -> None:
    @dataclass
    class Foo:
        value: int

    flex = FlexPack()

    provider_events = []

    @flex.bind
    async def provider() -> AsyncIterator[int]:
        provider_events.append("entered")
        try:
            yield 1
        finally:
            provider_events.append("exited")

    with flex:
        provider_events = []

        res = flex.invoke(Foo)
        assert isinstance(res, Foo)
        assert res.value == 1

        provider_events = ["entered"]

    provider_events = ["entered", "exited"]


def test_all_providers() -> None:
    @dataclass
    class Foo:
        val1: Annotated[int, "value1"]
        val2: Annotated[int, "value2"]
        val3: Annotated[int, "value3"]
        val4: Annotated[int, "value4"]

    flex = FlexPack()

    @flex.bind(target=Annotated[int, "value1"])
    def value1() -> int:
        return 1

    @flex.bind(target=Annotated[int, "value2"])
    async def value2() -> int:
        return 2

    @flex.bind(target=Annotated[int, "value3"])
    def value3() -> Iterator[int]:
        yield 3

    @flex.bind(target=Annotated[int, "value4"])
    async def value4() -> AsyncIterator[int]:
        yield 4

    with flex:
        res = flex.invoke(Foo)
        assert isinstance(res, Foo)
        assert res.val1 == 1
        assert res.val2 == 2
        assert res.val3 == 3
        assert res.val4 == 4


@pytest.mark.asyncio
async def test_async_all_providers() -> None:
    @dataclass
    class Foo:
        val1: Annotated[int, "value1"]
        val2: Annotated[int, "value2"]
        val3: Annotated[int, "value3"]
        val4: Annotated[int, "value4"]

    flex = FlexPack()

    @flex.bind(target=Annotated[int, "value1"])
    def value1() -> int:
        return 1

    @flex.bind(target=Annotated[int, "value2"])
    async def value2() -> int:
        return 2

    @flex.bind(target=Annotated[int, "value3"])
    def value3() -> Iterator[int]:
        yield 3

    @flex.bind(target=Annotated[int, "value4"])
    async def value4() -> AsyncIterator[int]:
        yield 4

    async with flex:
        res = await flex.ainvoke(Foo)
        assert isinstance(res, Foo)
        assert res.val1 == 1
        assert res.val2 == 2
        assert res.val3 == 3
        assert res.val4 == 4


def test_supports_all_func_invocations_sync() -> None:
    class Foo:
        pass

    def func1(foo: Foo) -> Foo:
        return foo

    async def func2(foo: Foo) -> Foo:
        return foo

    def func3(foo: Foo) -> Iterator[Foo]:
        yield foo

    async def func4(foo: Foo) -> AsyncIterator[Foo]:
        yield foo

    with FlexPack() as flex:
        res1 = flex.invoke(func1)
        res2 = flex.invoke(func2)
        res3 = flex.invoke(func3)
        res4 = flex.invoke(func4)
        assert_type(res1, Foo)
        assert_type(res2, Foo)
        assert_type(res3, Foo)
        assert_type(res4, Foo)
        assert isinstance(res1, Foo)
        assert isinstance(res2, Foo)
        assert isinstance(res3, Foo)
        assert isinstance(res4, Foo)


@pytest.mark.asyncio
async def test_supports_all_func_invocations_async() -> None:
    class Foo:
        pass

    def func1(foo: Foo) -> Foo:
        return foo

    async def func2(foo: Foo) -> Foo:
        return foo

    def func3(foo: Foo) -> Iterator[Foo]:
        yield foo

    async def func4(foo: Foo) -> AsyncIterator[Foo]:
        yield foo

    async with FlexPack() as flex:
        res1 = await flex.ainvoke(func1)
        res2 = await flex.ainvoke(func2)
        res3 = await flex.ainvoke(func3)
        res4 = await flex.ainvoke(func4)
        assert_type(res1, Foo)
        assert_type(res2, Foo)
        assert_type(res3, Foo)
        assert_type(res4, Foo)
        assert isinstance(res1, Foo)
        assert isinstance(res2, Foo)
        assert isinstance(res3, Foo)
        assert isinstance(res4, Foo)
