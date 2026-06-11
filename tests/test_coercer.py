"""Tests for coercer module."""

import pytest
from pydantic import BaseModel

from pydsettingsforge.coercer import coerce_env_values
from pydsettingsforge.exceptions import SettingsValidationError


class Item(BaseModel):
    name: str
    quantity: int


class ItemWithList(BaseModel):
    name: str
    tags: list[str]


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


class NestedModelWithListChild(BaseModel):
    children: list[ItemWithList]


class OptionalListModel(BaseModel):
    tags: list[str] | None = None


class OptionalUnionListModel(BaseModel):
    values: list[str] | int | None = None


class SingleValueListModel(BaseModel):
    hosts: list[str]


class EmptyListModel(BaseModel):
    hosts: list[str]


class NoCoercionModel(BaseModel):
    debug: bool
    port: int


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

    def test_json_decode_falls_back_to_split(self) -> None:
        data = {"hosts": "[bad json"}
        result = coerce_env_values(StringListModel, data)
        assert result == {"hosts": ["[bad json"]}

    def test_optional_union_with_list_picks_list_member(self) -> None:
        data = {"values": "a,b,c"}
        result = coerce_env_values(OptionalUnionListModel, data)
        assert result == {"values": ["a", "b", "c"]}


class TestSetTupleFrozenset:
    def test_set_of_strings(self) -> None:
        class M(BaseModel):
            tags: set[str]

        data = {"tags": "a,b,c"}
        result = coerce_env_values(M, data)
        assert result == {"tags": ["a", "b", "c"]}

    def test_frozenset_of_strings(self) -> None:
        class M(BaseModel):
            tags: frozenset[str]

        data = {"tags": "a,b,c"}
        result = coerce_env_values(M, data)
        assert result == {"tags": ["a", "b", "c"]}

    def test_tuple_variadic(self) -> None:
        class M(BaseModel):
            tags: tuple[str, ...]

        data = {"tags": "a,b,c"}
        result = coerce_env_values(M, data)
        assert result == {"tags": ["a", "b", "c"]}

    def test_tuple_fixed(self) -> None:
        class M(BaseModel):
            coords: tuple[int, int, int]

        data = {"coords": "1,2,3"}
        result = coerce_env_values(M, data)
        assert result == {"coords": ["1", "2", "3"]}


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

    def test_list_field_split(self) -> None:
        class Parent(BaseModel):
            child: list[str]

        data = {"child": "x,y,z"}
        result = coerce_env_values(Parent, data)
        assert result == {"child": ["x", "y", "z"]}

    def test_recurses_into_list_of_models_with_list_child(self) -> None:
        data = {
            "children": '[{"name": "a", "tags": "x,y,z"}, {"name": "b", "tags": "p,q"}]'
        }
        result = coerce_env_values(NestedModelWithListChild, data)
        assert result == {
            "children": [
                {"name": "a", "tags": ["x", "y", "z"]},
                {"name": "b", "tags": ["p", "q"]},
            ]
        }

    def test_recurses_into_nested_basemodel_with_dict(self) -> None:
        class Inner(BaseModel):
            metadata: dict[str, int]

        class Outer(BaseModel):
            inner: Inner

        data = {"inner": {"metadata": '{"a": 1, "b": 2}'}}
        result = coerce_env_values(Outer, data)
        assert result == {"inner": {"metadata": {"a": 1, "b": 2}}}


class TestPassthrough:
    def test_non_string_passthrough(self) -> None:
        data = {"debug": True, "port": 5432}
        result = coerce_env_values(NoCoercionModel, data)
        assert result == {"debug": True, "port": 5432}

    def test_unknown_fields_passthrough(self) -> None:
        data = {"hosts": "a,b", "extra": "value"}
        result = coerce_env_values(StringListModel, data)
        assert result == {"hosts": ["a", "b"], "extra": "value"}

    def test_list_field_already_list_passthrough(self) -> None:
        data = {"hosts": ["a", "b"]}
        result = coerce_env_values(StringListModel, data)
        assert result == {"hosts": ["a", "b"]}

    def test_dict_field_already_dict_passthrough(self) -> None:
        data = {"features": {"a": 1}}
        result = coerce_env_values(DictModel, data)
        assert result == {"features": {"a": 1}}

    def test_list_of_models_already_list_passthrough(self) -> None:
        data = {"children": [{"name": "x", "quantity": 1}]}
        result = coerce_env_values(NestedModel, data)
        assert result == {"children": [{"name": "x", "quantity": 1}]}

    def test_ambiguous_optional_union_passthrough(self) -> None:
        class AmbiguousOptModel(BaseModel):
            mode: int | str | None = None

        data = {"mode": "auto"}
        result = coerce_env_values(AmbiguousOptModel, data)
        assert result == {"mode": "auto"}


class TestCoerceOptOut:
    def test_coerce_env_false_returns_copy(self) -> None:
        data = {"hosts": "a,b,c"}
        result = coerce_env_values(StringListModel, data, coerce_env=False)
        assert result == {"hosts": "a,b,c"}
        assert result is not data

    def test_coerce_env_false_skips_list_split(self) -> None:
        data = {"ports": "80,443"}
        result = coerce_env_values(IntListModel, data, coerce_env=False)
        assert result == {"ports": "80,443"}

    def test_coerce_env_false_skips_dict_json(self) -> None:
        data = {"features": '{"x": 1}'}
        result = coerce_env_values(DictModel, data, coerce_env=False)
        assert result == {"features": '{"x": 1}'}


class TestErrors:
    def test_invalid_json_for_dict(self) -> None:
        with pytest.raises(SettingsValidationError, match="features"):
            coerce_env_values(DictModel, {"features": "{not valid"})

    def test_invalid_json_for_list_of_models(self) -> None:
        with pytest.raises(SettingsValidationError, match="children"):
            coerce_env_values(NestedModel, {"children": "[broken"})

    def test_list_of_models_rejects_non_list_json(self) -> None:
        with pytest.raises(SettingsValidationError, match="children"):
            coerce_env_values(NestedModel, {"children": '{"not": "a list"}'})
