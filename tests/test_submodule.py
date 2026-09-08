from __future__ import annotations

import pytest

from keel.errors import Missing
from keel.repo import Repo
from keel.submodule import SubmoduleSet


def with_child() -> tuple[SubmoduleSet, Repo]:
    parent = Repo.init()
    parent.commit({"app.py": b"parent"}, "parent base")
    child = Repo.init()
    child.commit({"lib.py": b"child v1"}, "child base")
    modules = SubmoduleSet(parent=parent)
    modules.add("vendor/lib", child)
    return modules, child


class TestPinning:
    def test_the_pin_starts_at_the_child_tip(self):
        modules, child = with_child()
        assert modules.pins["vendor/lib"] == (
            child.refs.current()
        )
        assert "in sync" in modules.status("vendor/lib")

    def test_the_pin_moves_only_on_purpose(self):
        modules, child = with_child()
        old_tip = child.refs.current()
        child.commit({"lib.py": b"child v2"}, "child grows")
        verdict = modules.update_pin(
            "vendor/lib", child.refs.current()
        )
        assert f"{old_tip[:8]} ->" in verdict

    def test_the_ghost_pin_is_a_treasure_map(self):
        modules, _ = with_child()
        with pytest.raises(Missing) as caught:
            modules.update_pin(
                "vendor/lib", "feedfacefeedfacefeed"
            )
        assert "collection already emptied" in str(
            caught.value
        )


class TestStatus:
    def test_ahead_is_the_dangerous_truth(self):
        modules, child = with_child()
        child.commit({"lib.py": b"child v2"}, "unshipped")
        status = modules.status("vendor/lib")
        assert "AHEAD of the pin" in status
        assert "finished and unshipped at once" in status

    def test_behind_prescribes_an_update(self):
        modules, child = with_child()
        child.commit({"lib.py": b"child v2"}, "child grows")
        modules.update_pin(
            "vendor/lib", child.refs.current()
        )
        child.refs.detach(
            child.graph.get(
                child.refs.branches["main"]
            ).parents[0]
        )
        assert "behind the pin" in modules.status(
            "vendor/lib"
        )

    def test_the_empty_set_is_first_party(self):
        parent = Repo.init()
        parent.commit({"a": b"x"}, "base")
        assert "every line is first-party" in (
            SubmoduleSet(parent=parent).report()
        )
