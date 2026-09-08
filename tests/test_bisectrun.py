from __future__ import annotations

import pytest

from keel.bisectrun import AutoBisect
from keel.commits import CommitGraph
from keel.errors import Invalid
from keel.objects import TREE, ObjectStore


def straight_line(count: int) -> tuple[CommitGraph, list[str]]:
    graph = CommitGraph(store=ObjectStore())
    addresses: list[str] = []
    parent: tuple[str, ...] = ()
    for number in range(count):
        tree = graph.store.put(TREE, f"t{number}".encode())
        commit = graph.create(tree, parent, f"c{number}")
        addresses.append(commit.address)
        parent = (commit.address,)
    return graph, addresses


class TestTheAutomatedHunt:
    def test_the_oracle_drives_to_the_culprit(self):
        graph, line = straight_line(20)
        breaking = 13

        def oracle(address: str) -> int:
            return 0 if line.index(address) < breaking else 1

        auto = AutoBisect(graph=graph, oracle=oracle)
        culprit = auto.run(line[0], line[-1])
        assert culprit == line[breaking]

    def test_exit_125_maps_to_skip_not_bad(self):
        graph, line = straight_line(8)

        def oracle(address: str) -> int:
            position = line.index(address)
            if position == 2:
                return 125
            return 0 if position < 5 else 1

        auto = AutoBisect(graph=graph, oracle=oracle)
        culprit = auto.run(line[0], line[-1])
        assert culprit == line[5]
        assert auto._verdict_for(line[2]) == "skip"
        assert auto.answers[line[2]] == 125

    def test_the_flip_flopping_oracle_is_untrustworthy(self):
        graph, line = straight_line(8)
        moods = {"count": 0}

        def oracle(address: str) -> int:
            del address
            moods["count"] += 1
            return moods["count"] % 2

        auto = AutoBisect(graph=graph, oracle=oracle)
        auto.answers[line[4]] = 0
        with pytest.raises(Invalid) as caught:
            for _ in range(10):
                auto._verdict_for(line[4])
        assert "changes its answer" in str(caught.value)


class TestTheEvidence:
    def test_the_culprit_arrives_with_its_transcript(self):
        graph, line = straight_line(16)

        def oracle(address: str) -> int:
            return 0 if line.index(address) < 11 else 1

        auto = AutoBisect(graph=graph, oracle=oracle)
        culprit = auto.run(line[0], line[-1])
        evidence = auto.evidence(culprit)
        assert "arrives with its evidence" in evidence
        assert evidence.count("oracle:") >= 3
        assert "why me, this is the answer" in evidence
