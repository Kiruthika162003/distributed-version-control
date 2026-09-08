"""Cherry detection graded on three picks: verbatim, reworded, reshaped.

The maintainer's question after a release is which of my
branch commits already landed upstream under other names,
and patch identity answers it by digesting the change
instead of the commit. The drill builds a branch with three
commits and lands them upstream three ways: one
cherry-picked verbatim, one cherry-picked with a completely
rewritten message, and one modified in flight so its diff
differs by a line. The grade: the verbatim pick matches, the
reworded pick matches too, proving the identity reads the
change and ignores the prose around it, and the reshaped
pick honestly fails to match, landing in pending, because a
diff that differs by a line is a different change no matter
what its message claims. Two landed, one pending, and the
pending one is the correct answer twice over: the branch
author must look at it, since what landed upstream is not
what they wrote.
"""

from __future__ import annotations

from keel.patchid import cherry_report
from keel.repo import Repo
from keel.witnesses.finding import Testimony

BASE = {"app.py": b"core\n", "lib.py": b"lib\n"}


def _stage() -> tuple[Repo, str, str]:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("branch")
    repo.refs.checkout("branch")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nalpha\n"}),
        "alpha work",
    )
    repo.commit(
        dict(
            BASE,
            **{
                "app.py": b"core\nalpha\n",
                "lib.py": b"lib\nbeta\n",
            },
        ),
        "beta work",
    )
    repo.commit(
        dict(
            BASE,
            **{
                "app.py": b"core\nalpha\n",
                "lib.py": b"lib\nbeta\n",
                "gamma.py": b"gamma\n",
            },
        ),
        "gamma work",
    )
    branch_tip = repo.refs.current()

    repo.refs.checkout("main")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nalpha\n"}),
        "alpha work",
    )
    repo.commit(
        dict(
            BASE,
            **{
                "app.py": b"core\nalpha\n",
                "lib.py": b"lib\nbeta\n",
            },
        ),
        "upstream prefers its own words entirely",
    )
    repo.commit(
        dict(
            BASE,
            **{
                "app.py": b"core\nalpha\n",
                "lib.py": b"lib\nbeta\n",
                "gamma.py": b"gamma\nreshaped\n",
            },
        ),
        "gamma work",
    )
    upstream_tip = repo.refs.current()
    return repo, branch_tip, upstream_tip


def run() -> Testimony:
    repo, branch_tip, upstream_tip = _stage()
    report = cherry_report(repo, branch_tip, upstream_tip)
    landed_messages = sorted(
        repo.graph.get(address).message
        for address in report["landed"]
    )
    pending_messages = [
        repo.graph.get(address).message
        for address in report["pending"]
    ]
    numbers = {
        "landed": len(report["landed"]),
        "pending": len(report["pending"]),
        "reworded_still_matched": (
            "beta work" in landed_messages
        ),
        "reshaped_honestly_missed": (
            pending_messages == ["gamma work"]
        ),
    }
    holds = (
        numbers["landed"] == 2
        and numbers["pending"] == 1
        and numbers["reworded_still_matched"]
        and numbers["reshaped_honestly_missed"]
    )
    return Testimony(
        witness="patchidmatch",
        claim=(
            "the verbatim pick matches, the reworded pick "
            "matches because identity digests the change "
            "and ignores the prose, and the reshaped pick "
            "lands in pending, since a diff that differs "
            "by a line is a different change no matter "
            "what its message claims"
        ),
        numbers=numbers,
        holds=holds,
    )
