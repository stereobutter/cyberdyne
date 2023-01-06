from trio_util import AsyncValue
from typing import TypeVar, Generic, Callable, Union, NoReturn
from collections.abc import Iterable

T = TypeVar("T")

FieldT = Union["Field[T]", "DerivedField[T]"]


class Field(Generic[T]):
    """Descriptor that wraps a `trio_util.AsyncValue` and updates dependant values."""

    def __init__(self, initial_value: T):
        self._initial_value = initial_value
        self._dependants = []

    def _add_dependant(self, field: "DerivedField"):
        self._dependants.append(field)

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
        for dependant in self._dependants:
            dependant._update(obj)


class DerivedField(Generic[T]):
    """Descriptor that wraps a `trio_util.AsyncValue` that gets updated
    when values it depends on change."""

    def __init__(
        self, fn: Callable[..., T], depends_on: Union[FieldT, Iterable[FieldT]]
    ):
        self._fn = fn
        self._depends_on: Iterable[FieldT] = (
            depends_on if isinstance(depends_on, Iterable) else (depends_on,)
        )

    def _add_dependant(self, field: "DerivedField"):
        for dependency in self._depends_on:
            dependency._add_dependant(field)

    def __set_name__(self, cls, name):
        self.name = name
        for field in self._depends_on:
            field._add_dependant(self)

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
