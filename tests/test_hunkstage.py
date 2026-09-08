from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.hunkstage import HunkSession

BASE = "def handler():\n    validate()\n    respond()\n"
WORKING = (
    "def handler():\n"
    "    validate()\n"
    "    print('debug')\n"
    "    respond()\n"
    "    audit()\n"
)


def session() -> HunkSession:
    return HunkSession(
        base_text=BASE, working_text=WORKING
    )


class TestTheMenu:
    def test_the_two_changes_appear_as_separate_hunks(self):
        chosen = session()
        assert len(chosen.hunks) == 2
        assert all("left" in row for row in chosen.menu())

    def test_an_identical_file_has_nothing_to_pick(self):
        with pytest.raises(Invalid) as caught:
            HunkSession(base_text=BASE, working_text=BASE)
        assert "nothing to pick apart" in str(caught.value)


class TestPicking:
    def test_the_fix_commits_without_the_debugging(self):
        chosen = session()
        audit_index = next(
            index
            for index, hunk in enumerate(chosen.hunks)
            if any("audit()" in line for line in hunk.new_lines)
        )
        chosen.pick(audit_index)
        staged = chosen.staged_text()
        assert "audit()" in staged
        assert "print('debug')" not in staged

    def test_nothing_picked_is_theater(self):
        with pytest.raises(Invalid) as caught:
            session().staged_text()
        assert "would be theater" in str(caught.value)

    def test_the_menu_is_bounded(self):
        with pytest.raises(Invalid):
            session().pick(9)


class TestTheReceipt:
    def test_both_futures_are_named(self):
        chosen = session()
        audit_index = next(
            index
            for index, hunk in enumerate(chosen.hunks)
            if any("audit()" in line for line in hunk.new_lines)
        )
        chosen.pick(audit_index)
        receipt = chosen.receipt()
        assert "1 hunk(s) will commit" in receipt
        assert "1 remain in the working copy" in receipt
        assert "that difference is the entire point" in receipt

    def test_leaving_reverses_a_pick(self):
        chosen = session()
        chosen.pick(0)
        chosen.leave(0)
        with pytest.raises(Invalid):
            chosen.staged_text()
