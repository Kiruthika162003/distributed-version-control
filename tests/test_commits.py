from __future__ import annotations

import pytest

from keel.commits import CommitGraph
from keel.errors import Invalid, Missing
from keel.objects import TREE, ObjectStore


def graph() -> CommitGraph:
    return CommitGraph(store=ObjectStore())


def tree(chart: CommitGraph, label: str) -> str:
    return chart.store.put(TREE, label.encode())


class TestCreation:
    def test_parents_are_part_of_the_address(self):
        chart = graph()
        base = chart.create(tree(chart, "t0"), (), "root")
        child = chart.create(
            tree(chart, "t0"), (base.address,), "root"
        )
        assert base.address != child.address

    def test_sequence_replaces_the_wall_clock(self):
        chart = graph()
        first = chart.create(tree(chart, "a"), (), "one")
        second = chart.create(tree(chart, "b"), (), "two")
        assert (first.sequence, second.sequence) == (0, 1)

    def test_the_empty_message_is_refused(self):
        with pytest.raises(Invalid) as caught:
            graph().create("t", (), "  ")
        assert "say the thing" in str(caught.value)

    def test_ghost_parents_are_refused(self):
        with pytest.raises(Missing):
            graph().create("t", ("feedface",), "orphan")


class TestAncestry:
    def test_ancestry_is_transitive(self):
        chart = graph()
        a = chart.create(tree(chart, "a"), (), "a")
        b = chart.create(tree(chart, "b"), (a.address,), "b")
        c = chart.create(tree(chart, "c"), (b.address,), "c")
        assert chart.is_ancestor(a.address, c.address)
        assert not chart.is_ancestor(c.address, a.address)

    def test_the_log_walks_newest_first(self):
        chart = graph()
        a = chart.create(tree(chart, "a"), (), "a")
        b = chart.create(tree(chart, "b"), (a.address,), "b")
        assert [c.message for c in chart.log(b.address)] == [
            "b", "a",
        ]


class TestMergeBase:
    def test_the_fork_point_is_found(self):
        chart = graph()
        base = chart.create(tree(chart, "base"), (), "base")
        left = chart.create(
            tree(chart, "l"), (base.address,), "left"
        )
        right = chart.create(
            tree(chart, "r"), (base.address,), "right"
        )
        assert chart.merge_base(
            left.address, right.address
        ) == base.address

    def test_the_fast_forward_base_is_the_older_tip(self):
        chart = graph()
        a = chart.create(tree(chart, "a"), (), "a")
        b = chart.create(tree(chart, "b"), (a.address,), "b")
        assert chart.merge_base(a.address, b.address) == (
            a.address
        )

    def test_strangers_share_no_ancestor(self):
        chart = graph()
        a = chart.create(tree(chart, "a"), (), "a")
        b = chart.create(tree(chart, "b"), (), "b")
        with pytest.raises(Missing) as caught:
            chart.merge_base(a.address, b.address)
        assert "strangers, not branches" in str(caught.value)

    def test_the_criss_cross_is_refused_not_coin_flipped(self):
        chart = graph()
        root = chart.create(tree(chart, "0"), (), "root")
        a = chart.create(tree(chart, "a"), (root.address,), "a")
        b = chart.create(tree(chart, "b"), (root.address,), "b")
        left = chart.create(
            tree(chart, "l"), (a.address, b.address), "merge lb"
        )
        right = chart.create(
            tree(chart, "r"), (b.address, a.address), "merge rl"
        )
        with pytest.raises(Invalid) as caught:
            chart.merge_base(left.address, right.address)
        assert "criss-cross history" in str(caught.value)
        assert "returns weekly" in str(caught.value)
