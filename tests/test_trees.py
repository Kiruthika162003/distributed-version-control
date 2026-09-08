from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.objects import BLOB, ObjectStore
from keel.trees import TreeBuilder, diff_trees


def builder() -> TreeBuilder:
    return TreeBuilder(store=ObjectStore())


def snapshot(built: TreeBuilder, files: dict[str, bytes]) -> str:
    blobs = {
        path: built.store.put(BLOB, content)
        for path, content in files.items()
    }
    return built.write_tree(blobs)


PROJECT = {
    "README": b"docs",
    "src/main.py": b"print(1)",
    "src/util.py": b"helpers",
    "src/deep/inner.py": b"nested",
}


class TestRoundTrip:
    def test_write_then_read_restores_every_path(self):
        built = builder()
        address = snapshot(built, PROJECT)
        files = built.read_tree(address)
        assert sorted(files) == sorted(PROJECT)

    def test_equal_directories_share_an_address(self):
        built = builder()
        first = snapshot(built, PROJECT)
        second = snapshot(built, dict(PROJECT))
        assert first == second

    def test_a_deep_edit_changes_only_the_spine(self):
        built = builder()
        before = snapshot(built, PROJECT)
        edited = dict(PROJECT, **{"src/deep/inner.py": b"changed"})
        after = snapshot(built, edited)
        assert before != after
        assert built.entry_at(before, "README") == (
            built.entry_at(after, "README")
        )

    def test_entry_at_walks_nested_paths(self):
        built = builder()
        address = snapshot(built, PROJECT)
        blob = built.entry_at(address, "src/deep/inner.py")
        assert built.store.get(blob) == b"nested"


class TestRefusals:
    def test_dirty_paths_are_refused(self):
        built = builder()
        for path in ("/abs", "trail/", "a//b", ""):
            with pytest.raises(Invalid):
                built.write_tree({path: "feedface"})

    def test_one_name_one_nature(self):
        built = builder()
        blob = built.store.put(BLOB, b"x")
        with pytest.raises(Invalid) as caught:
            built.write_tree({"src": blob, "src/main.py": blob})
        assert "one name, one nature" in str(caught.value)

    def test_the_missing_path_is_named(self):
        built = builder()
        address = snapshot(built, PROJECT)
        with pytest.raises(Missing) as caught:
            built.entry_at(address, "src/ghost.py")
        assert "src/ghost.py is not in this tree" in str(
            caught.value
        )

    def test_a_file_is_not_a_directory(self):
        built = builder()
        address = snapshot(built, PROJECT)
        with pytest.raises(Invalid) as caught:
            built.entry_at(address, "README/inside")
        assert "a file, not a directory" in str(caught.value)


class TestDiff:
    def test_the_three_change_kinds_are_split(self):
        built = builder()
        before = snapshot(built, PROJECT)
        edited = dict(PROJECT)
        del edited["README"]
        edited["src/util.py"] = b"rewritten"
        edited["NEWS"] = b"fresh"
        after = snapshot(built, edited)
        assert diff_trees(built, before, after) == {
            "README": "removed",
            "NEWS": "added",
            "src/util.py": "modified",
        }

    def test_identical_trees_diff_to_nothing(self):
        built = builder()
        address = snapshot(built, PROJECT)
        assert diff_trees(built, address, address) == {}

    def test_the_empty_side_reads_as_all_added(self):
        built = builder()
        address = snapshot(built, {"a.txt": b"x"})
        assert diff_trees(built, None, address) == {
            "a.txt": "added"
        }
