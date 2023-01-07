import pytest
from cyberdyne.blackboards import Field, DependentField


class Example:
    a = Field(1)
    b = Field(2)
    c = DependentField(lambda a, b: a + b, depends_on=(a, b))
    d = DependentField(lambda c: 2 * c, depends_on=c)


def test_initial_field_values():
    example = Example()
    assert example.a.value == 1


def test_initial_derived_field_values():
    example = Example()
    assert example.c.value == 3


def test_derived_fields_update():
    example = Example()
    example.a = 2
    assert example.c.value == 4
    assert example.d.value == 8


def test_field_object_identity():
    example = Example()

    a = example.a
    c = example.c
    example.a = 2
    assert a is example.a
    assert c is example.c


def test_setting_derived_field_fails():
    example = Example()
    with pytest.raises(AttributeError):
        example.c = 2  # type: ignore
