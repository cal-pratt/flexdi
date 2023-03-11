from typing import Any, Callable, Type, TypeVar, Union

from typing_extensions import Literal

# Note, in 3.10+ we can start using TypeAlias
Func = Union[Type[Any], Callable[..., Any]]
Instance = Any
FuncT = TypeVar("FuncT", bound=Callable[..., Any])


ScopeName = Literal["application", "request"]
SCOPE_NAMES = ["application", "request"]
