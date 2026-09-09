# The credential-shaped strings in this file are synthetic fixtures. They exist
# to give the scanner something to match and they authenticate against nothing.
# No real password, key, token, or personal data appears anywhere in this file.
"""The worst landing ever attempted, and every gate still speaks once.

The one-trip rule is a promise repeated in three gauntlets,
and the witness stress-tests it with a landing engineered
to fail everywhere at once: a frozen branch, missing
reviews, a forbidden path, a stolen-out lock, a budget
overdraft, a labeled credential, and a case collision, all
in one push. The measurement counts voices: eleven gates
live across the three gauntlets, and all eleven must
appear in the held page, the failing ones in their own
words and the passing ones saying ok, because the promise
is not that failures are listed but that nothing waits in
ambush behind them. Two more properties ride the same
run: the secret is never quoted anywhere in the page, and
the harbormaster's headline counts exactly three
objecting gauntlets, which together make the worst landing
the best possible test of the paperwork.
"""

from __future__ import annotations

from keel.acl import AccessTable
from keel.budgets import BudgetBook
from keel.codeowners import OwnersFile
from keel.customs import Customs
from keel.departures import Departures
from keel.errors import Conflict
from keel.filelocks import LockOffice
from keel.freeze import FreezeBoard
from keel.gatekeeper import Gatekeeper, PushRequest
from keel.harbormaster import Harbormaster
from keel.protect import BranchGuard, Protection
from keel.repo import Repo
from keel.witnesses.finding import Testimony

GATE_MARKS = (
    "freeze:",
    "force:",
    "reviews:",
    "owners:",
    "message:",
    "access:",
    "locks:",
    "budgets:",
    "secrets:",
    "portability:",
    "license:",
)


def _doomed_harbor() -> tuple[Harbormaster, PushRequest, dict]:
    repo = Repo.init()
    repo.commit(
        {
            "infra/deploy.sh": b"deploy\n",
            "assets/logo.bin": b"x" * 90,
        },
        "base",
    )
    guard = BranchGuard()
    guard.protect(
        Protection(pattern="main", required_reviews=2)
    )
    board = FreezeBoard()
    board.freeze("main", "the release cut", "priya")
    keeper = Gatekeeper(
        guard=guard,
        board=board,
        owners=OwnersFile.parse("infra/ team-infra\n"),
    )
    access = AccessTable()
    access.enroll("team-infra", "priya")
    access.grant("infra/", "team-infra")
    locks = LockOffice()
    locks.take(
        "assets/logo.bin", "devi", "recoloring"
    )
    budgets = BudgetBook()
    budgets.set_allowance("assets/", 100)
    master = Harbormaster(
        gatekeeper=keeper,
        customs=Customs(
            repo=repo,
            access=access,
            locks=locks,
            budgets=budgets,
        ),
        departures=Departures(),
    )
    request = PushRequest(
        branch="main",
        submitter="dana",
        messages=("no reviews, no shame",),
        touched_paths=(
            "infra/deploy.sh",
            "assets/logo.bin",
        ),
    )
    proposed = {
        "infra/deploy.sh": b"deploy\nrogue\n",
        "assets/logo.bin": b"x" * 200,
        "Conf.ini": b"password=hunter2\n",
        "conf.ini": b"other case\n",
    }
    return master, request, proposed


def run() -> Testimony:
    master, request, proposed = _doomed_harbor()
    held_page = ""
    try:
        master.land(request, proposed)
    except Conflict as refusal:
        held_page = str(refusal)
    voices = sum(
        1
        for mark in GATE_MARKS
        if mark in held_page
    )
    numbers = {
        "gates_alive": len(GATE_MARKS),
        "voices_heard": voices,
        "gauntlets_objecting": (
            "3 of 3 gauntlet(s) object" in held_page
        ),
        "secret_quoted": "hunter2" in held_page,
    }
    holds = (
        numbers["voices_heard"] == 11
        and numbers["gauntlets_objecting"]
        and not numbers["secret_quoted"]
    )
    return Testimony(
        witness="gauntlettrip",
        claim=(
            "the landing engineered to fail everywhere "
            "still hears all eleven gates in one trip, "
            "the harbormaster counts three objecting "
            "gauntlets, and the secret is never quoted "
            "anywhere in the paperwork"
        ),
        numbers=numbers,
        holds=holds,
    )
