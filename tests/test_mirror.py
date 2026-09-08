from __future__ import annotations

import pytest

from keel.errors import Conflict, Missing
from keel.mirror import Mirror
from keel.repo import Repo


def build() -> tuple[Repo, Mirror]:
    source = Repo.init()
    source.commit({"app.py": b"core\n"}, "begin")
    source.commit({"app.py": b"core\nmore\n"}, "grow")
    source.branch_from_head("feature")
    mirror = Mirror(source=source, replica=Repo.init())
    return source, mirror


class TestFaithfulness:
    def test_the_first_sync_copies_the_branch_table(self):
        source, mirror = build()
        receipt = mirror.sync()
        assert "pointer(s) moved" in receipt
        assert mirror.verify() == (
            "faithful: every branch matches to the "
            "address"
        )
        tip = source.refs.branches["main"]
        assert mirror.replica.files_at(tip)["app.py"] == (
            b"core\nmore\n"
        )

    def test_the_second_sync_ships_only_the_new(self):
        source, mirror = build()
        mirror.sync()
        source.refs.checkout("main")
        source.commit(
            {"app.py": b"core\nmore\nnew\n"}, "newest"
        )
        receipt = mirror.sync()
        assert "3 object(s) shipped" in receipt
        assert mirror.verify().startswith("faithful")

    def test_deletions_at_the_source_retire_the_copy(
        self,
    ):
        source, mirror = build()
        mirror.sync()
        source.refs.checkout("main")
        source.refs.delete("feature")
        mirror.sync()
        assert (
            "feature" not in mirror.replica.refs.branches
        )
        assert any(
            entry.startswith("retired feature")
            for entry in mirror.journal
        )

    def test_verify_names_unsynced_drift(self):
        source, mirror = build()
        mirror.sync()
        source.refs.checkout("main")
        source.commit(
            {"app.py": b"core\nmore\nnew\n"}, "newest"
        )
        page = mirror.verify()
        assert page.startswith("1 drift(s):")
        assert "main: source" in page


class TestDirectWrites:
    def test_a_direct_write_stops_the_shredder(self):
        source, mirror = build()
        mirror.sync()
        older = source.graph.get(
            source.refs.branches["main"]
        ).parents[0]
        mirror.replica.refs.move(
            "main",
            older,
            reason="someone pushed to the mirror",
            force=True,
        )
        with pytest.raises(Conflict) as caught:
            mirror.sync()
        message = str(caught.value)
        assert "written to directly on main" in message
        assert "paper shredder" in message

    def test_reclaim_is_a_decision_with_a_name(self):
        source, mirror = build()
        mirror.sync()
        older = source.graph.get(
            source.refs.branches["main"]
        ).parents[0]
        mirror.replica.refs.move(
            "main",
            older,
            reason="misdirected push",
            force=True,
        )
        entry = mirror.reclaim("main")
        assert entry.startswith("RECLAIMED main")
        assert "by decision, not by schedule" in entry
        mirror.sync()
        assert mirror.verify().startswith("faithful")

    def test_reclaiming_a_faithful_branch_is_refused(
        self,
    ):
        _source, mirror = build()
        mirror.sync()
        with pytest.raises(Missing) as caught:
            mirror.reclaim("main")
        assert "exactly where the mirror left it" in str(
            caught.value
        )
