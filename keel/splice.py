"""The splice: two histories joined end to end, the seam checked first.

Histories get severed for ordinary reasons, the archived
project resumed in a fresh repository, the import that
started from a snapshot, and the splice repairs the cut:
the elder line replayed from its root, then the younger
line grafted on where its root would have stood, one
continuous history in a fresh repository with the seam
invisible to every tool that walks it. The seam check is
the module's law: the younger root's snapshot must equal
the elder tip's byte for byte, because a splice over a gap
invents history, and invented history poisons every blame
and bisect that later crosses it believing. Both lines
must be linear, merges being meetings this operation has
no minutes for, and the payoff is stated in the receipt:
blame now walks across the seam, which is the entire
reason anyone splices.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Invalid
from keel.repo import Repo


def _chain(repo: Repo, tip: str) -> list[Commit]:
    found = []
    cursor = tip
    while True:
        commit = repo.graph.get(cursor)
        if len(commit.parents) > 1:
            raise Invalid(
                f"{cursor[:8]} is a merge; the splice "
                "has no minutes for meetings, both "
                "lines must be linear"
            )
        found.append(commit)
        if not commit.parents:
            found.reverse()
            return found
        cursor = commit.parents[0]


def splice(
    elder: Repo, younger: Repo
) -> tuple[Repo, str]:
    elder_chain = _chain(elder, elder.refs.current())
    younger_chain = _chain(
        younger, younger.refs.current()
    )
    seam_elder = elder.files_at(
        elder_chain[-1].address
    )
    seam_younger = younger.files_at(
        younger_chain[0].address
    )
    if seam_elder != seam_younger:
        differing = sorted(
            path
            for path in set(seam_elder)
            | set(seam_younger)
            if seam_elder.get(path)
            != seam_younger.get(path)
        )
        raise Invalid(
            "the seam does not match: "
            + ", ".join(differing)
            + " differ between the elder tip and the "
            "younger root; a splice over a gap "
            "invents history, and invented history "
            "poisons every blame that crosses it "
            "believing"
        )
    joined = Repo.init()
    previous: str | None = None
    replayed = 0
    for commit in elder_chain:
        parents = (previous,) if previous else ()
        created = joined.commit_with_parents(
            elder.files_at(commit.address),
            commit.message,
            parents,
        )
        previous = created.address
        replayed += 1
    seam_address = previous
    for commit in younger_chain[1:]:
        created = joined.commit_with_parents(
            younger.files_at(commit.address),
            commit.message,
            (previous,),
        )
        previous = created.address
        replayed += 1
    joined.refs.create_branch("main", previous)
    joined.refs.checkout("main")
    report = (
        f"spliced {len(elder_chain)} elder and "
        f"{len(younger_chain) - 1} younger commit(s) "
        f"into one line of {replayed}, seam at "
        f"{seam_address[:8]}; blame now walks across "
        "it, which is the entire reason anyone "
        "splices"
    )
    return joined, report
