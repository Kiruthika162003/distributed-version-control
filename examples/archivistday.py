"""An archivist's day: the tour, the trail, the ages, and the health.

A newcomer arrives at an old repository and reads it the
way an archivist would: the computed tour first, then one
file's trail across its renames, then the age census that
says where the fresh paint is, and the health report to
close, every page computed live from the history rather
than from documents that stopped being true. Run with:
python -m examples.archivistday
"""

from __future__ import annotations

from keel.codeage import report as age_report
from keel.firstday import tour
from keel.followpath import narrate as follow_narrate
from keel.repo import Repo
from keel.repohealth import health_report


def build_archive() -> Repo:
    repo = Repo.init()
    repo.commit(
        {
            "utils.py": b"helpers\n",
            "config.txt": b"mode=calm\n",
        },
        "the founding",
    )
    repo.commit(
        {
            "utils.py": b"helpers\nmore\n",
            "config.txt": b"mode=calm\n",
        },
        "grow the helpers",
    )
    repo.commit(
        {
            "toolbox.py": b"helpers\nmore\n",
            "config.txt": b"mode=calm\n",
        },
        "rename to toolbox",
    )
    repo.commit(
        {
            "toolbox.py": b"helpers\nmore\nsharp\n",
            "config.txt": b"mode=calm\n",
        },
        "sharpen the toolbox",
    )
    return repo


def main() -> int:
    repo = build_archive()
    print(tour(repo).split("\n\n")[0])
    print()
    print(
        follow_narrate(
            repo, repo.refs.current(), "toolbox.py"
        )
    )
    print()
    print(
        age_report(
            repo, repo.refs.current()
        ).splitlines()[1]
    )
    print()
    health = health_report(repo)
    print(health.splitlines()[0])
    print(health.split("\n\n")[-1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
