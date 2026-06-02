"""Tests for coercer module."""

import pytest
from pydantic import BaseModel

from pydsettingsforge.coercer import coerce_env_values
from pydsettingsforge.exceptions import SettingsValidationError


class Item(BaseModel):
    name: str
    quantity: int


class StringListModel(BaseModel):
    hosts: list[str]


class IntListModel(BaseModel):
    ports: list[int]


class DictModel(BaseModel):
    features: dict[str, int]


class JsonListModel(BaseModel):
    items: list[int]


class NestedModel(BaseModel):
    children: list[Item]


class OptionalListModel(BaseModel):
    tags: list[str] | None = None


class SingleValueListModel(BaseModel):
    hosts: list[str]


class EmptyListModel(BaseModel):
    hosts: list[str]


class NoCoercionModel(BaseModel):
    debug: bool
    port: int


class CoercerTestBase:
    pass


class TestCoerceList:
    def test_list_of_strings(self) -> None:
        data = {"hosts": "a,b,c"}
        result = coerce_env_values(StringListModel, data)
        assert result == {"hosts": ["a", "b", "c"]}

    def test_list_of_ints_split_into_strings(self) -> None:
        data = {"ports": "80,443,5432"}
        result = coerce_env_values(IntListModel, data)
        assert result == {"ports": ["80", "443", "5432"]}

    def test_whitespace_stripped(self) -> None:
        data = {"hosts": "a, b ,  c"}
        result = coerce_env_values(StringListModel, data)
        assert result == {"hosts": ["a", "b", "c"]}

    def test_single_value(self) -> None:
        data = {"hosts": "single.example.com"}
        result = coerce_env_values(SingleValueListModel, data)
        assert result == {"hosts": ["single.example.com"]}

    def test_empty_string(self) -> None:
        data = {"hosts": ""}
        result = coerce_env_values(EmptyListModel, data)
        assert result == {"hosts": []}

    def test_json_list(self) -> None:
        data = {"items": "[1, 2, 3]"}
        result = coerce_env_values(JsonListModel, data)
        assert result == {"items": [1, 2, 3]}

    def test_custom_separator(self) -> None:
        data = {"hosts": "a;b;c"}
        result = coerce_env_values(StringListModel, data, list_separator=";")
        assert result == {"hosts": ["a", "b", "c"]}

    def test_optional_list_with_value(self) -> None:
        data = {"tags": "alpha,beta"}
        result = coerce_env_values(OptionalListModel, data)
        assert result == {"tags": ["alpha", "beta"]}

    def test_optional_list_missing(self) -> None:
        data: dict = {}
        result = coerce_env_values(OptionalListModel, data)
        assert result == {}


class TestCoerceDict:
    def test_dict_from_json(self) -> None:
        data = {"features": '{"x": 1, "y": 2}'}
        result = coerce_env_values(DictModel, data)
        assert result == {"features": {"x": 1, "y": 2}}


class TestCoerceNested:
    def test_list_of_nested_models(self) -> None:
        data = {
            "children": '[{"name": "a", "quantity": 1}, {"name": "b", "quantity": 2}]'
        }
        result = coerce_env_values(NestedModel, data)
        assert result == {
            "children": [
                {"name": "a", "quantity": 1},
                {"name": "b", "quantity": 2},
            ]
        }

    def test_recurses_into_nested_basemodel(self) -> None:
        class Parent(BaseModel):
            child: list[str]

        data = {"child": "x,y,z"}
        result = coerce_env_values(Parent, data)
        assert result == {"child": ["x", "y", "z"]}

    def test_recurses_into_nested_basemodel_with_dict(self) -> None:
        class Inner(BaseModel):
            tags: list[str]

        class Outer(BaseModel):
            inner: Inner

        data = {"inner": {"tags": "a,b,c"}}
        result = coerce_env_values(Outer, data)
        assert result == {"inner": {"tags": ["a", "b", "c"]}}


class TestPassthrough:
    def test_non_string_passthrough(self) -> None:
        data = {"debug": True, "port": 5432}
        result = coerce_env_values(NoCoercionModel, data)
        assert result == {"debug": True, "port": 5432}

    def test_unknown_fields_passthrough(self) -> None:
        data = {"hosts": "a,b", "extra": "value"}
        result = coerce_env_values(StringListModel, data)
        assert result == {"hosts": ["a", "b"], "extra": "value"}


class TestErrors:
    def test_invalid_json_for_list(self) -> None:
        with pytest.raises(SettingsValidationError, match="items"):
            coerce_env_values(JsonListModel, {"items": "[bad json"})

    def test_invalid_json_for_dict(self) -> None:
        with pytest.raises(SettingsValidationError, match="features"):
            coerce_env_values(DictModel, {"features": "{not valid"})

    def test_invalid_json_for_nested_list(self) -> None:
        with pytest.raises(SettingsValidationError, match="children"):
            coerce_env_values(NestedModel, {"children": "[broken"})
