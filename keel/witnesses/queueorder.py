"""The same four branches queued twice, order reversed, verdicts swapped.

Merge queues are sometimes described as fair, and the drill
measures what the word actually buys. Four branches: two
that touch the same line two ways, one harmless, one the
gate dislikes. Run one queues the first contender ahead and
it lands while the second bounces off the conflict; run two
reverses them and the verdicts swap exactly, the former
loser landing clean and the former winner bouncing off the
ground the loser now owns. Everything else holds still: the
harmless branch lands in both runs, the gated branch
bounces in both, and the landed count is two both times.
The measurement says the quiet part in numbers: the queue
does not adjudicate merit, it adjudicates arrival, and the
only fairness it sells is that the rule is the same for
everyone standing in line.
"""

from __future__ import annotations

from keel.mergequeue import MergeQueue
from keel.repo import Repo
from keel.witnesses.finding import Testimony

BASE = {
    "app.py": b"core\n",
    "docs.md": b"start\n",
    "lib.py": b"lib\n",
}


def _arena() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    for name, files in (
        ("east", {"app.py": b"core\neast\n"}),
        ("west", {"app.py": b"core\nwest\n"}),
        ("docs", {"docs.md": b"start\nmore\n"}),
        ("gated", {"lib.py": b"lib\nforbidden\n"}),
    ):
        repo.branch_from_head(name)
        repo.refs.checkout(name)
        repo.commit(dict(BASE, **files), f"{name} work")
        repo.refs.checkout("main")
    return repo


def _gate(files: dict[str, bytes]) -> str | None:
    if b"forbidden" in files.get("lib.py", b""):
        return "lib.py smells forbidden"
    return None


def _run(order: tuple[str, ...]) -> dict[str, str]:
    repo = _arena()
    queue = MergeQueue(repo=repo)
    for branch in order:
        queue.submit(branch, "someone")
    queue.process(_gate)
    return {
        entry.branch: entry.state
        for entry in queue.entries
    }


def run() -> Testimony:
    east_first = _run(("east", "west", "docs", "gated"))
    west_first = _run(("west", "east", "docs", "gated"))
    numbers = {
        "east_first": (
            east_first["east"],
            east_first["west"],
        ),
        "west_first": (
            west_first["east"],
            west_first["west"],
        ),
        "docs_landed_both_runs": (
            east_first["docs"] == "landed"
            and west_first["docs"] == "landed"
        ),
        "gated_bounced_both_runs": (
            east_first["gated"] == "bounced"
            and west_first["gated"] == "bounced"
        ),
    }
    holds = (
        numbers["east_first"] == ("landed", "bounced")
        and numbers["west_first"] == ("bounced", "landed")
        and numbers["docs_landed_both_runs"]
        and numbers["gated_bounced_both_runs"]
    )
    return Testimony(
        witness="queueorder",
        claim=(
            "reversing the queue swaps the contenders' "
            "verdicts exactly while the harmless and the "
            "gated hold still; the queue adjudicates "
            "arrival, not merit, and the only fairness it "
            "sells is one rule for everyone in line"
        ),
        numbers=numbers,
        holds=holds,
    )
