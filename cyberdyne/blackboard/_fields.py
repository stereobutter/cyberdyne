from trio_util import AsyncValue
from typing import TypeVar, Generic, Callable, Union, NoReturn
from collections.abc import Iterable


T = TypeVar("T")
FieldT = Union["Field[T]", "DerivedField[T]"]


class Field(Generic[T]):
    """Descriptor for an attribute with the ability to wait for a value or
    transition.

    Example::

        >>> class Blackboard:
        >>>     a = Field(0)
        >>> ...
        >>> blackboard = Blackboard()
        >>> ...
        >>> # blackboard.a returns an `AsyncValue`
        >>> await blackboard.a.wait_value(...)
        >>> ...
        >>> # sets the value of the underlying `AsyncValue`
        >>> blackboard.a = 1
    """

    def __init__(self, initial_value: T):
        self._initial_value = initial_value
        self._dependents = []

    def _add_dependent(self, field: "DerivedField"):
        self._dependents.append(field)

    def __set_name__(self, cls: type, name: str):
        self.name = name

    def _ensure_initial_value(self, obj):
        if self.name not in obj.__dict__:
            obj.__dict__[self.name] = AsyncValue(self._initial_value)

    def __get__(self, obj, cls: type) -> AsyncValue[T]:
        self._ensure_initial_value(obj)
        return obj.__dict__[self.name]

    def __set__(self, obj, value: T) -> None:
        self._ensure_initial_value(obj)
        async_value = obj.__dict__[self.name]
        async_value.value = value
        for dependent in self._dependents:
            dependent._update(obj)


class DerivedField(Generic[T]):
    """Descriptor for an attribute that depends on other attributes with the
    ability to wait for a value or transition.

    Example::

        >>> class Blackboard:
        >>>     a = Field(1)
        >>>     b = Field(1)
        >>>     c = DerivedField(lambda a, b: a+b, depends_on=(a, b))
        >>>     # a derived field may also depend on other derived fields.
        >>>     d = DerivedField(lambda c: 2*c, depends_on=c)
    """

    def __init__(
        self,
        fn: Callable[..., T],
        depends_on: Union[FieldT, Iterable[FieldT]],
    ):
        self._fn = fn
        self._depends_on: Iterable[FieldT] = (
            depends_on if isinstance(depends_on, Iterable) else (depends_on,)
        )

    def _add_dependent(self, field: "DerivedField"):
        for dependency in self._depends_on:
            dependency._add_dependent(field)

    def __set_name__(self, cls, name):
        self.name = name
        for field in self._depends_on:
            field._add_dependent(self)

    def _ensure_initial_value(self, obj):
        if self.name not in obj.__dict__:
            initial_value = self._compute_value(obj)
            obj.__dict__[self.name] = AsyncValue(initial_value)

    def _compute_value(self, obj) -> T:
        async_values = [getattr(obj, field.name) for field in self._depends_on]
        new_value = self._fn(*(async_value.value for async_value in async_values))
        return new_value

    def _update(self, obj):
        self._ensure_initial_value(obj)
        async_value = obj.__dict__[self.name]
        async_value.value = self._compute_value(obj)

    def __get__(self, obj, cls) -> AsyncValue[T]:
        self._ensure_initial_value(obj)
        return obj.__dict__[self.name]

    def __set__(self, obj, value: "DerivedField") -> NoReturn:
        raise AttributeError("can't set attribute for derived fields")
