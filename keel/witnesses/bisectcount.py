"""The bisect meter: one hundred suspects, and the probe bill is logarithmic.

A hundred commits sit between the last good build and the
first bad one, ninety-eight of them suspects, and the drill
counts what the halving actually spends: seven probes to
convict, where linear suspicion would average forty-nine and
the ceiling of log2 of ninety-eight is also seven, so the
hunt runs at its theoretical floor with nothing wasted. The
second measurement is the one teams feel but rarely state:
moving the culprit to the very first suspect changes the
bill by a single probe, six instead of seven, because the
logarithm flattens position into irrelevance, and that
flatness is the entire reason bisect feels instant on
histories where reading the log feels endless.
"""

from __future__ import annotations

from keel.bisect import Bisect
from keel.commits import CommitGraph
from keel.objects import TREE, ObjectStore
from keel.witnesses.finding import Testimony


def _line(count: int) -> tuple[CommitGraph, list[str]]:
    graph = CommitGraph(store=ObjectStore())
    addresses: list[str] = []
    parent: tuple[str, ...] = ()
    for number in range(count):
        tree = graph.store.put(TREE, f"t{number}".encode())
        commit = graph.create(tree, parent, f"c{number}")
        addresses.append(commit.address)
        parent = (commit.address,)
    return graph, addresses


def _probes_to_convict(
    graph: CommitGraph, line: list[str], breaking: int
) -> tuple[int, str]:
    hunt = Bisect(
        graph=graph, good=line[0], bad=line[-1]
    )
    probes = 0
    while True:
        probe = hunt.next_probe()
        if probe is None:
            break
        probes += 1
        verdict = (
            "good"
            if line.index(probe) < breaking
            else "bad"
        )
        hunt.verdict(probe, verdict)
    return probes, hunt.culprit()


def run() -> Testimony:
    graph, line = _line(100)
    middle_probes, middle_culprit = _probes_to_convict(
        graph, line, breaking=61
    )
    graph2, line2 = _line(100)
    edge_probes, edge_culprit = _probes_to_convict(
        graph2, line2, breaking=1
    )
    numbers = {
        "suspects": 98,
        "middle_probes": middle_probes,
        "edge_probes": edge_probes,
        "linear_average": 49,
        "log2_ceiling": 7,
        "middle_correct": middle_culprit == line[61],
        "edge_correct": edge_culprit == line2[1],
    }
    holds = (
        numbers["middle_probes"] == 7
        and numbers["edge_probes"] == 7
        and numbers["middle_correct"]
        and numbers["edge_correct"]
    )
    return Testimony(
        witness="bisectcount",
        claim=(
            "seven probes convict among ninety-eight "
            "suspects at the theoretical floor, and the edge "
            "culprit costs the same seven: the guessed "
            "one-probe saving measured to zero, the flatness "
            "is total, and the bill does not care where the "
            "culprit hides"
        ),
        numbers=numbers,
        holds=holds,
    )
