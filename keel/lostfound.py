"""The lost and found: unreachable commits shelved, described, claimable.

The reflog is the first line of recovery and it can be
trimmed, so the lost and found is the second: a census of
commits that exist in the graph but are reachable from no
branch and no tag, each shelved with its subject, its file
count, and its sequence, newest first, because the commit
someone is missing is almost always the one they lost most
recently. Claiming is the whole point of finding: a claim
points a new branch at the orphan and it stops being lost,
with the receipt noting how much history comes back with
it, since an orphan often anchors a chain and the claimant
deserves to know they recovered a week and not a commit.
The empty shelf is reported as the good news it is, and
the census never deletes, that being the collector's job
and the exact opposite of this module's.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid, Missing
from keel.repo import Repo
from keel.tags import TagStore


@dataclass(frozen=True)
class FoundItem:
    address: str
    subject: str
    sequence: int
    file_count: int

    def line(self) -> str:
        return (
            f"  {self.address[:8]} (seq "
            f"{self.sequence}): {self.subject!r}, "
            f"{self.file_count} file(s)"
        )


def _reachable(
    repo: Repo, tags: TagStore | None
) -> set[str]:
    found: set[str] = set()
    tips = list(repo.refs.branches.values())
    if tags is not None:
        tips.extend(
            tag.target for tag in tags.tags.values()
        )
    for tip in tips:
        found |= repo.graph.ancestors(tip)
    return found


def shelf(
    repo: Repo, tags: TagStore | None = None
) -> list[FoundItem]:
    reachable = _reachable(repo, tags)
    items = []
    for address, commit in repo.graph.commits.items():
        if address in reachable:
            continue
        items.append(
            FoundItem(
                address=address,
                subject=commit.message.splitlines()[0],
                sequence=commit.sequence,
                file_count=len(repo.files_at(address)),
            )
        )
    items.sort(key=lambda item: -item.sequence)
    return items


def listing(
    repo: Repo, tags: TagStore | None = None
) -> str:
    items = shelf(repo, tags)
    if not items:
        return (
            "the shelf is empty; nothing reachable "
            "was lost, which is the good news it "
            "sounds like"
        )
    lines = [
        f"{len(items)} unreachable commit(s), newest "
        "first:"
    ]
    lines.extend(item.line() for item in items)
    lines.append(
        "claim any of them by name; finding was "
        "only half the job"
    )
    return "\n".join(lines)


def claim(
    repo: Repo,
    address: str,
    branch: str,
    tags: TagStore | None = None,
) -> str:
    items = {
        item.address for item in shelf(repo, tags)
    }
    if address not in items:
        raise Missing(
            f"{address[:8]} is not on the shelf; "
            "either it was never lost or someone "
            "claimed it first"
        )
    if branch in repo.refs.branches:
        raise Invalid(
            f"{branch} exists; claims go to fresh "
            "branches so recoveries never overwrite "
            "the living"
        )
    recovered = len(repo.graph.ancestors(address))
    repo.refs.create_branch(branch, address)
    return (
        f"{branch} claims {address[:8]}; "
        f"{recovered} commit(s) of history come "
        "back with it, a week and not a commit"
    )
