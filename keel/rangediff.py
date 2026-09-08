"""Range diff: comparing a branch with its own past self, change by change.

After a rebase the branch is new commits top to bottom, and
the review question is not "what does it change" but "what
changed about the changes", and each side is measured from
its own base because the rebased branch stands on new ground
by definition, a fact the first single-base draft forgot and
the tests caught when main's own commit appeared as an
arrival: which patches survived intact,
which were modified in flight, which vanished, which
appeared. The comparison pairs old and new commits by patch
identity first, exact survivors cost nothing to verify, then
matches the remainder by message as a weaker hint with the
weakness stated, and whatever pairs by message but differs
by patch id is the interesting bucket, modified in flight,
the one reviewers actually need to reread. Unpaired commits
land as dropped or added, and the report orders survivors
first, modifications second, arrivals and departures last,
because the reviewer's time follows that gradient of
surprise.
"""

from __future__ import annotations

from keel.errors import Invalid
from keel.patchid import patch_id
from keel.repo import Repo


def _line(repo: Repo, tip: str, stop: str) -> list[str]:
    commits: list[str] = []
    cursor = tip
    while cursor != stop:
        commit = repo.graph.get(cursor)
        if len(commit.parents) != 1:
            raise Invalid(
                "range diff walks single-parent lines; "
                "merges compare as themselves, not as ranges"
            )
        commits.append(cursor)
        cursor = commit.parents[0]
    commits.reverse()
    return commits


def range_diff(
    repo: Repo,
    old_tip: str,
    new_tip: str,
    old_base: str,
    new_base: str,
) -> dict[str, list[str]]:
    old_line = _line(repo, old_tip, old_base)
    new_line = _line(repo, new_tip, new_base)
    old_ids = {
        patch_id(repo, address): address
        for address in old_line
    }
    new_ids = {
        patch_id(repo, address): address
        for address in new_line
    }
    survived = [
        old_ids[shared]
        for shared in old_ids
        if shared in new_ids
    ]
    old_rest = {
        address: repo.graph.get(address).message
        for pid, address in old_ids.items()
        if pid not in new_ids
    }
    new_rest = {
        address: repo.graph.get(address).message
        for pid, address in new_ids.items()
        if pid not in old_ids
    }
    modified: list[str] = []
    for old_address, message in list(old_rest.items()):
        twin = next(
            (
                new_address
                for new_address, new_message in (
                    new_rest.items()
                )
                if new_message == message
            ),
            None,
        )
        if twin is not None:
            modified.append(
                f"{old_address[:8]} -> {twin[:8]}: "
                f"{message} (paired by message, the weaker "
                "hint)"
            )
            del old_rest[old_address]
            del new_rest[twin]
    return {
        "survived": sorted(
            f"{a[:8]}: {repo.graph.get(a).message}"
            for a in survived
        ),
        "modified": modified,
        "dropped": sorted(
            f"{a[:8]}: {m}" for a, m in old_rest.items()
        ),
        "added": sorted(
            f"{a[:8]}: {m}" for a, m in new_rest.items()
        ),
    }


def narrate_range_diff(
    repo: Repo,
    old_tip: str,
    new_tip: str,
    old_base: str,
    new_base: str,
) -> str:
    buckets = range_diff(
        repo, old_tip, new_tip, old_base, new_base
    )
    lines = [
        f"{len(buckets['survived'])} survived, "
        f"{len(buckets['modified'])} modified in flight, "
        f"{len(buckets['dropped'])} dropped, "
        f"{len(buckets['added'])} added"
    ]
    for label in ("survived", "modified", "dropped", "added"):
        for entry in buckets[label]:
            lines.append(f"  {label}: {entry}")
    lines.append(
        "modified in flight is the bucket reviewers reread; "
        "the reviewer's time follows the gradient of surprise"
    )
    return "\n".join(lines)
