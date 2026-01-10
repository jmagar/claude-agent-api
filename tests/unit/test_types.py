"""Unit tests for shared type aliases."""

from pathlib import Path


def test_json_value_alias_has_no_duplicate_entries() -> None:
    """Ensure JsonValue alias does not repeat union members."""
    contents = Path("apps/api/types.py").read_text(encoding="utf-8")
    start = contents.find("JsonValue: TypeAlias")
    end = contents.find(")", start)
    assert start != -1
    assert end != -1

    block = contents[start:end]

    assert block.count("| bool") == 1
    assert block.count("| int") == 1
    assert block.count("| float") == 1
    assert block.count("| str") == 1
    assert block.count('| list["JsonValue"]') == 1
    assert block.count('| dict[str, "JsonValue"]') == 1
