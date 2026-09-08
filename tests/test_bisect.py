from __future__ import annotations

import pytest

from keel.bisect import Bisect
from keel.commits import CommitGraph
from keel.errors import Invalid
from keel.objects import TREE, ObjectStore


def straight_line(count: int) -> tuple[CommitGraph, list[str]]:
    graph = CommitGraph(store=ObjectStore())
    addresses: list[str] = []
    parent: tuple[str, ...] = ()
    for number in range(count):
        tree = graph.store.put(TREE, f"t{number}".encode())
        commit = graph.create(tree, parent, f"commit {number}")
        addresses.append(commit.address)
        parent = (commit.address,)
    return graph, addresses


def hunt(breaking_at: int, count: int = 16) -> tuple[Bisect, str]:
    graph, line = straight_line(count)
    bisect = Bisect(
        graph=graph, good=line[0], bad=line[-1]
    )
    while True:
        probe = bisect.next_probe()
        if probe is None:
            break
        position = line.index(probe)
        bisect.verdict(
            probe,
            "bad" if position >= breaking_at else "good",
        )
    return bisect, line[breaking_at]


class TestTheHunt:
    def test_the_culprit_is_found_in_logarithmic_probes(self):
        bisect, culprit = hunt(breaking_at=11)
        assert bisect.culprit() == culprit
        assert bisect.probes <= 5

    def test_the_first_commit_after_good_can_be_guilty(self):
        bisect, culprit = hunt(breaking_at=1)
        assert bisect.culprit() == culprit

    def test_the_narration_answers_how_much_longer(self):
        bisect, _ = hunt(breaking_at=7)
        assert "probe(s) owed" in bisect.log[0]
        assert any(
            "candidate(s) remain" in line for line in bisect.log
        )
        assert bisect.culprit()
        assert "after" in bisect.log[-1]


class TestTheInvariants:
    def test_unrelated_endpoints_search_nothing(self):
        graph, line = straight_line(3)
        island = graph.create(
            graph.store.put(TREE, b"island"), (), "island"
        )
        with pytest.raises(Invalid) as caught:
            Bisect(
                graph=graph,
                good=island.address,
                bad=line[-1],
            )
        assert "searches nothing" in str(caught.value)

    def test_contradictions_are_refused_with_both_named(self):
        graph, line = straight_line(8)
        bisect = Bisect(graph=graph, good=line[0], bad=line[-1])
        bisect.verdict(line[3], "bad")
        with pytest.raises(Invalid) as caught:
            bisect.verdict(line[5], "good")
        assert "innocent commit" in str(caught.value)

    def test_verdicts_come_from_a_short_menu(self):
        graph, line = straight_line(4)
        bisect = Bisect(graph=graph, good=line[0], bad=line[-1])
        with pytest.raises(Invalid):
            bisect.verdict(line[2], "maybe")

    def test_an_unfinished_hunt_refuses_to_accuse(self):
        graph, line = straight_line(16)
        bisect = Bisect(graph=graph, good=line[0], bad=line[-1])
        with pytest.raises(Invalid) as caught:
            bisect.culprit()
        assert "the hunt is not finished" in str(caught.value)


class TestSkips:
    def test_a_skip_steps_aside_without_shrinking(self):
        graph, line = straight_line(8)
        bisect = Bisect(graph=graph, good=line[0], bad=line[-1])
        probe = bisect.next_probe()
        bounds_before = (bisect.low, bisect.high)
        bisect.verdict(probe, "skip")
        assert (bisect.low, bisect.high) == bounds_before
        assert probe not in bisect._testable_untested()

    def test_skips_around_the_culprit_end_in_a_range(self):
        graph, line = straight_line(5)
        bisect = Bisect(graph=graph, good=line[0], bad=line[-1])
        bisect.verdict(line[2], "skip")
        bisect.verdict(line[1], "good")
        bisect.verdict(line[3], "bad")
        with pytest.raises(Invalid) as caught:
            bisect.culprit()
        assert "a range, not a guess" in str(caught.value)
