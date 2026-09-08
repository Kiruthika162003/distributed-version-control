"""Line survivorship: who still speaks in the tip, measured by blame.

Commit counts flatter the busy; survivorship honors the
lasting. The drill builds a file through four commits, a
founding of four lines, an expansion of three, a rewrite
that replaces two of the founder's lines, and a polish
that adds one, then blames every line at the tip and bills
each surviving line to the commit that last wrote it. The
guess: the founder keeps two of eight lines, the expansion
keeps its three, the rewrite two, the polish one. Measured
exactly so, and the arithmetic carries the lesson worth
the witness: the founder wrote half the file's history and
owns a quarter of its present, because history is written
by everyone and the present is owned by whoever wrote
last. Survivorship is the number code review folklore
calls ownership, and it decays by rewrite, not by time.
"""

from __future__ import annotations

from keel.blame import blame
from keel.repo import Repo
from keel.witnesses.finding import Testimony


def _story() -> tuple[Repo, dict[str, str]]:
    repo = Repo.init()
    names = {}
    founding = (
        b"alpha\nbeta\ngamma\ndelta\n"
    )
    commit = repo.commit(
        {"saga.txt": founding}, "the founding"
    )
    names[commit.address] = "founding"
    expansion = founding + b"epsilon\nzeta\neta\n"
    commit = repo.commit(
        {"saga.txt": expansion}, "the expansion"
    )
    names[commit.address] = "expansion"
    rewrite = (
        b"alpha\nBETA REWRITTEN\nGAMMA REWRITTEN\n"
        b"delta\nepsilon\nzeta\neta\n"
    )
    commit = repo.commit(
        {"saga.txt": rewrite}, "the rewrite"
    )
    names[commit.address] = "rewrite"
    polish = rewrite + b"theta\n"
    commit = repo.commit(
        {"saga.txt": polish}, "the polish"
    )
    names[commit.address] = "polish"
    return repo, names


def run() -> Testimony:
    repo, names = _story()
    rows = blame(repo, repo.refs.current(), "saga.txt")
    survived: dict[str, int] = {}
    for row in rows:
        label = names[row.commit]
        survived[label] = survived.get(label, 0) + 1
    numbers = {
        "lines_at_tip": len(rows),
        "founding": survived.get("founding", 0),
        "expansion": survived.get("expansion", 0),
        "rewrite": survived.get("rewrite", 0),
        "polish": survived.get("polish", 0),
    }
    holds = (
        numbers["lines_at_tip"] == 8
        and numbers["founding"] == 2
        and numbers["expansion"] == 3
        and numbers["rewrite"] == 2
        and numbers["polish"] == 1
    )
    return Testimony(
        witness="survivorship",
        claim=(
            "the founder wrote half the file's history "
            "and owns a quarter of its present: history "
            "is written by everyone, the present is "
            "owned by whoever wrote last, and ownership "
            "decays by rewrite, not by time"
        ),
        numbers=numbers,
        holds=holds,
    )
