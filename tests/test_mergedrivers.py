from __future__ import annotations

import pytest

from keel.attributes import AttributesFile
from keel.errors import Invalid
from keel.mergedrivers import DriverBench, union_merge

RULES = AttributesFile.parse(
    "CHANGELOG merge=union\n"
    "gen/ merge=ours\n"
    "upstream.lock merge=theirs\n"
    "*.png binary\n"
    "logo.png merge=union\n"
    "cursed.txt merge=magic\n"
)


def bench() -> DriverBench:
    return DriverBench(attributes=RULES)


class TestUnion:
    def test_every_entry_survives_in_base_order(self):
        merged = union_merge(
            "one\ntwo\n",
            "one\ntwo\nours-entry\n",
            "one\ntwo\ntheirs-entry\n",
        )
        assert merged == (
            "one\ntwo\nours-entry\ntheirs-entry\n"
        )

    def test_lines_dropped_by_both_sides_stay_dropped(
        self,
    ):
        merged = union_merge(
            "one\nold\ntwo\n",
            "one\ntwo\n",
            "one\ntwo\n",
        )
        assert merged == "one\ntwo\n"

    def test_a_line_one_side_keeps_is_kept(self):
        merged = union_merge(
            "one\nkeeper\n",
            "one\nkeeper\n",
            "one\n",
        )
        assert "keeper" in merged

    def test_binary_paths_refuse_the_zipper(self):
        with pytest.raises(Invalid) as caught:
            bench().merge("logo.png", "a", "b", "c")
        assert "two different jackets" in str(caught.value)


class TestOaths:
    def test_ours_takes_a_side_and_signs_the_log(self):
        table = bench()
        merged, receipt = table.merge(
            "gen/parser.py",
            "base\n",
            "ours\n",
            "theirs\n",
        )
        assert merged == "ours\n"
        assert "took one side whole" in receipt
        assert table.oath_log == [receipt]

    def test_theirs_is_the_other_oath(self):
        table = bench()
        merged, _receipt = table.merge(
            "upstream.lock",
            "base\n",
            "ours\n",
            "theirs\n",
        )
        assert merged == "theirs\n"
        assert len(table.oath_log) == 1


class TestDiff3Default:
    def test_clean_merges_say_so(self):
        _merged, receipt = bench().merge(
            "notes.txt",
            "one\ntwo\n",
            "ONE\ntwo\n",
            "one\nTWO\n",
        )
        assert receipt == "notes.txt: diff3 merged clean"

    def test_conflicts_are_left_for_a_person(self):
        _merged, receipt = bench().merge(
            "notes.txt",
            "one\n",
            "ours-one\n",
            "theirs-one\n",
        )
        assert "left conflicts for a person" in receipt


class TestTheRoster:
    def test_a_stranger_driver_is_refused_with_the_bench(
        self,
    ):
        with pytest.raises(Invalid) as caught:
            bench().merge("cursed.txt", "a", "b", "c")
        message = str(caught.value)
        assert "names driver 'magic'" in message
        assert "diff3, union, ours, theirs" in message
