import collections.abc
import inspect
from functools import lru_cache
from typing import Any, Sequence, Tuple, Type, get_args, get_origin


@lru_cache(maxsize=None)
def get_cached_class_args(clazz: Type[Any]) -> Tuple[Type[Any], Sequence[Type[Any]]]:
    """
    Helper function to inspect class types.
    For a given class, determine the class to instantiate, and any generic arguments.
    e.g.
    Dict[str, int] -> (dict, (str, int))
    Foo -> (Foo, (,))
    """

    # If the type is generic, this will be the class to use to instantiate
    # This will be None if the class is not generic.
    clazz_origin = get_origin(clazz) or clazz

    # If the type is generic, this will be the generic parameters
    # This will be an empty tuple if the class is not generic.
    clazz_args = get_args(clazz)

    return clazz_origin, clazz_args


def provider_return_type(obj: Any) -> Any:
    signature = inspect.signature(obj)
    return_type = signature.return_annotation
    clazz_origin, clazz_args = get_cached_class_args(return_type)

    if clazz_origin is collections.abc.Iterator:
        return clazz_args[0]
    elif clazz_origin is collections.abc.AsyncIterator:
        return clazz_args[0]

    return return_type
