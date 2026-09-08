"""Archaeology day: blame, the pickaxe, line history, and the narrated hunt.

Run with: python -m examples.archaeologyday
"""

from __future__ import annotations

from keel.bisectrun import AutoBisect
from keel.blame import blame, summarize
from keel.linehistory import narrate_range
from keel.pickaxe import survival_story
from keel.repo import Repo


def dig_site() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"def target():\n    return use_old()"},
        "birth",
    )
    repo.commit(
        {
            "app.py": (
                b"import os\n"
                b"def target():\n    return use_old()"
            )
        },
        "imports grew",
    )
    repo.commit(
        {
            "app.py": (
                b"import os\n"
                b"def target():\n    return use_new()"
            )
        },
        "the migration",
    )
    return repo


def main() -> int:
    repo = dig_site()
    tip = repo.refs.current()

    rows = blame(repo, tip, "app.py")
    print(f"blame:   {summarize(rows)}")

    story = survival_story(repo, tip, b"use_old")
    print(f"pickaxe: {story.splitlines()[0]}")

    ranged = narrate_range(repo, tip, "app.py", 2, 3)
    print(f"range:   {ranged.splitlines()[0]}")

    line: list[str] = []
    cursor: str | None = tip
    while cursor is not None:
        line.append(cursor)
        parents = repo.graph.get(cursor).parents
        cursor = parents[0] if parents else None
    line.reverse()
    breaking = next(
        index
        for index, a in enumerate(line)
        if repo.graph.get(a).message == "the migration"
    )

    def oracle(address: str) -> int:
        return 0 if line.index(address) < breaking else 1

    auto = AutoBisect(graph=repo.graph, oracle=oracle)
    culprit = auto.run(line[0], line[-1])
    print(
        f"bisect:  culprit is "
        f"{repo.graph.get(culprit).message!r} with "
        f"{len(auto.transcript)} transcript line(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
