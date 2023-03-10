from typing import Any, Callable, Optional, Type, TypeVar, Union, overload

Clazz = TypeVar("Clazz", bound=Type[Any])


@overload
def implicitbinding() -> Callable[[Clazz], Clazz]:
    ...


@overload
def implicitbinding(clazz: Clazz) -> Clazz:
    ...


def implicitbinding(
    clazz: Optional[Clazz] = None,
) -> Union[Clazz, Callable[[Clazz], Clazz]]:
    """
    This decorator allows marking as class as being okay for dependency
    injection even if it hasn't been explicitly bound by the graph instance.
    This helps users reduce boilerplate in their main methods for their classes
    which can be trivially resolved by the graph.

    This decorator adds a class attribute to the class definition which
    acts as an indicator during graph resolution that this class may be
    implicitly resolved.
    """

    def wrapper(_clazz: Clazz) -> Clazz:
        setattr(_clazz, "_flexdi_implicitbinding", object())
        return _clazz

    return wrapper(clazz) if clazz else wrapper


def is_implicitbinding(obj: Any) -> bool:
    return hasattr(obj, "_flexdi_implicitbinding")
