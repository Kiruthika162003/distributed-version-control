"""A repository pushed through text and back, graded address by address.

The export stream is supposed to be a complete second copy
of the truth, and the witness holds it to the strong form
of complete: a five-commit history with an edit, an
addition, and a deletion is exported to text, imported into
a fresh repository, and then every commit address on the
original line must exist in the rebuilt graph with the same
tree address, because content addressing makes equality
checkable to the byte and there is no excuse for settling
for looks similar. The guess before measuring was that
addresses would survive, since the stream carries messages
and file bytes and the import replays them in order; it
held, five of five identical, and one property earns the
emphasis: equality of the tip address alone would have
proven all of it, ancestry being part of every address, but
the witness checks all five anyway because a proof a reader
can follow line by line beats a proof that asks them to
believe in hashes.
"""

from __future__ import annotations

from keel.exportimport import fast_export, fast_import
from keel.repo import Repo
from keel.witnesses.finding import Testimony


def _original() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"core\n", "notes.md": b"n\n"},
        "begin",
    )
    repo.commit(
        {"app.py": b"core\nmore\n", "notes.md": b"n\n"},
        "edit app",
    )
    repo.commit(
        {
            "app.py": b"core\nmore\n",
            "notes.md": b"n\n",
            "extra.py": b"x\n",
        },
        "add extra",
    )
    repo.commit(
        {
            "app.py": b"core\nmore\n",
            "extra.py": b"x\n",
        },
        "drop the notes",
    )
    repo.commit(
        {
            "app.py": b"core\nmore\nend\n",
            "extra.py": b"x\n",
        },
        "finish",
    )
    return repo


def run() -> Testimony:
    original = _original()
    tip = original.refs.current()
    stream = fast_export(original, tip)
    rebuilt = fast_import(stream)
    line = original.graph.log(tip)
    matched = 0
    trees_matched = 0
    for commit in line:
        twin = rebuilt.graph.commits.get(commit.address)
        if twin is not None:
            matched += 1
            if twin.tree == commit.tree:
                trees_matched += 1
    numbers = {
        "commits_on_the_line": len(line),
        "addresses_survived": matched,
        "trees_survived": trees_matched,
        "stream_lines": len(stream.splitlines()),
        "tip_identical": (
            rebuilt.refs.branches.get("main") == tip
        ),
    }
    holds = (
        numbers["commits_on_the_line"] == 5
        and numbers["addresses_survived"] == 5
        and numbers["trees_survived"] == 5
        and numbers["tip_identical"]
    )
    return Testimony(
        witness="cloneproof",
        claim=(
            "five of five addresses and trees survive "
            "the trip through text; the tip alone would "
            "have proven it, ancestry being part of "
            "every address, but a proof a reader can "
            "follow beats a proof that asks for faith "
            "in hashes"
        ),
        numbers=numbers,
        holds=holds,
    )
