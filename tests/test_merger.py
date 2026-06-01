"""Tests for merger module."""

from settingsforge.merger import deep_merge


class TestDeepMerge:
    def test_flat_merge(self) -> None:
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self) -> None:
        base = {"db": {"host": "localhost", "port": 5432}}
        override = {"db": {"port": 3306}}
        result = deep_merge(base, override)
        assert result == {"db": {"host": "localhost", "port": 3306}}

    def test_override_dict_with_scalar(self) -> None:
        base = {"db": {"host": "localhost"}}
        override = {"db": "simple"}
        result = deep_merge(base, override)
        assert result == {"db": "simple"}

    def test_override_scalar_with_dict(self) -> None:
        base = {"db": "simple"}
        override = {"db": {"host": "localhost"}}
        result = deep_merge(base, override)
        assert result == {"db": {"host": "localhost"}}

    def test_does_not_mutate_inputs(self) -> None:
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        base_copy = {"a": {"b": 1}}
        deep_merge(base, override)
        assert base == base_copy

    def test_empty_base(self) -> None:
        result = deep_merge({}, {"a": 1})
        assert result == {"a": 1}

    def test_empty_override(self) -> None:
        result = deep_merge({"a": 1}, {})
        assert result == {"a": 1}

    def test_both_empty(self) -> None:
        result = deep_merge({}, {})
        assert result == {}

    def test_deeply_nested(self) -> None:
        base = {"a": {"b": {"c": 1, "d": 2}}}
        override = {"a": {"b": {"d": 3, "e": 4}}}
        result = deep_merge(base, override)
        assert result == {"a": {"b": {"c": 1, "d": 3, "e": 4}}}
