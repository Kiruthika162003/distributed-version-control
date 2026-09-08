"""A policy day: the gauntlet, the freeze, the override, and the queue.

One afternoon of governance: a clean push walks every gate,
a release freeze slams down and a push bounces with the
freeze and the missing reviews listed in one trip, an
emergency lands through the loud override, and the merge
queue finishes the day by landing what combines and
bouncing what does not. Run with:
python -m examples.policyday
"""

from __future__ import annotations

from keel.codeowners import OwnersFile
from keel.freeze import FreezeBoard
from keel.gatekeeper import Gatekeeper, PushRequest
from keel.mergequeue import MergeQueue
from keel.protect import BranchGuard, Protection
from keel.repo import Repo

REVIEWED = (
    "Land the payment retry\n"
    "\n"
    "Reviewed-by: priya\n"
    "Reviewed-by: devi\n"
)

BASE = {"src/app.py": b"core\n", "docs/guide.md": b"g\n"}


def main() -> int:
    guard = BranchGuard()
    guard.protect(
        Protection(pattern="main", required_reviews=2)
    )
    board = FreezeBoard()
    keeper = Gatekeeper(
        guard=guard,
        board=board,
        owners=OwnersFile.parse(
            "src/ team-core\ndocs/ team-docs\n"
        ),
    )

    clean = keeper.receive(
        PushRequest(
            branch="main",
            submitter="dana",
            messages=(REVIEWED,),
            touched_paths=("src/app.py",),
        )
    )
    print(clean.splitlines()[0])

    print(
        "freeze:  "
        + board.freeze("main", "the release cut", "priya")
    )
    refused = keeper.receive(
        PushRequest(
            branch="main",
            submitter="dana",
            messages=("quick tweak, no reviews",),
            touched_paths=("src/app.py",),
        )
    )
    print(refused.splitlines()[0])
    print(refused.splitlines()[1])
    print(refused.splitlines()[3])

    print(
        "over:    "
        + board.override(
            "main", "dana", "priya", "HOT-99"
        )
    )
    print("board:   " + board.report().splitlines()[0])
    board.lift("main", "priya")

    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    for name, files in (
        ("retry", {"src/app.py": b"core\nretry\n"}),
        ("clash", {"src/app.py": b"core\nclash\n"}),
        ("docs", {"docs/guide.md": b"g\nmore\n"}),
    ):
        repo.branch_from_head(name)
        repo.refs.checkout(name)
        repo.commit(dict(BASE, **files), f"{name} work")
        repo.refs.checkout("main")
    queue = MergeQueue(repo=repo)
    for name in ("retry", "clash", "docs"):
        queue.submit(name, "dana")
    print("queue:   " + queue.process(lambda _files: None))
    print(queue.report().splitlines()[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
