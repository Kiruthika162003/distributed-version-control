"""A harbor day: one desk, three gauntlets, two landings, no ambushes.

The morning landing fails everywhere at once and every gate
still speaks: the freeze, the missing reviews, the held
lock, the budget, and the credential that never gets
quoted. The afternoon landing arrives with its paperwork in
order and clears in one visit. Between them, the lock is
released and the freeze lifted, each with its receipt.
Run with: python -m examples.harborday
"""

from __future__ import annotations

from keel.acl import AccessTable
from keel.budgets import BudgetBook
from keel.customs import Customs
from keel.departures import Departures
from keel.errors import Conflict
from keel.filelocks import LockOffice
from keel.freeze import FreezeBoard
from keel.gatekeeper import Gatekeeper, PushRequest
from keel.harbormaster import Harbormaster
from keel.protect import BranchGuard, Protection
from keel.repo import Repo

REVIEWED = (
    "Land the retry logic\n"
    "\n"
    "Reviewed-by: priya\n"
    "Reviewed-by: devi\n"
)

BASE = {
    "src/app.py": b"core\n",
    "assets/logo.bin": b"x" * 90,
}


def main() -> int:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    guard = BranchGuard()
    guard.protect(
        Protection(pattern="main", required_reviews=2)
    )
    board = FreezeBoard()
    board.freeze("main", "the release cut", "priya")
    locks = LockOffice()
    locks.take("assets/logo.bin", "devi", "recoloring")
    budgets = BudgetBook()
    budgets.set_allowance("assets/", 100)
    master = Harbormaster(
        gatekeeper=Gatekeeper(guard=guard, board=board),
        customs=Customs(
            repo=repo,
            access=AccessTable(),
            locks=locks,
            budgets=budgets,
        ),
        departures=Departures(),
    )

    doomed = PushRequest(
        branch="main",
        submitter="dana",
        messages=("quick tweak",),
        touched_paths=(
            "src/app.py",
            "assets/logo.bin",
        ),
    )
    doomed_files = {
        "src/app.py": b"core\ntweak\n",
        "assets/logo.bin": b"x" * 200,
        "conf.ini": b"password=hunter2\n",
    }
    try:
        master.land(doomed, doomed_files)
    except Conflict as held:
        page = str(held)
        print(page.splitlines()[0])
        gates = sum(
            1
            for line in page.splitlines()
            if "[REFUSE]" in line
            or "[HOLD]" in line
        )
        print(
            f"gates objecting: {gates}; the secret "
            f"quoted: {'hunter2' in page}"
        )

    print("lift:    " + board.lift("main", "priya"))
    print(
        "release: "
        + locks.release("assets/logo.bin", "devi")
    )

    cleared = PushRequest(
        branch="main",
        submitter="dana",
        messages=(REVIEWED,),
        touched_paths=("src/app.py",),
    )
    page = master.land(
        cleared,
        dict(BASE, **{"src/app.py": b"core\nretry\n"}),
    )
    print(page.splitlines()[0])
    print(page.splitlines()[-1].strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
