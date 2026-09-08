"""Patch identity: the same change wears different addresses, and cherry knows.

A commit's address changes with its parents, so a fix
cherry-picked to a release branch and the original on main
are strangers by address while being the same change by any
human reading. The patch id closes the gap: it digests the
commit's diff against its first parent, path by path, old
content to new content, ignoring everything positional, so
the same change lands on the same id wherever it sits in
history. Cherry detection is then set arithmetic: the commits
on a branch whose patch ids already appear upstream are
landed, whatever their addresses say, and the report splits
landed from pending because "what is left to merge" is the
question release managers actually ask. The id is blind on
merges by design and says so, since a merge's diff depends on
which parent you ask, and an identity that changes with the
question is not an identity.
"""

from __future__ import annotations

import hashlib

from keel.errors import Invalid
from keel.repo import Repo


def patch_id(repo: Repo, address: str) -> str:
    commit = repo.graph.get(address)
    if len(commit.parents) > 1:
        raise Invalid(
            f"{address[:8]} is a merge; its diff depends on "
            "which parent you ask, and an identity that "
            "changes with the question is not an identity"
        )
    if commit.parents:
        parent_files = repo.files_at(commit.parents[0])
    else:
        parent_files = {}
    own_files = repo.files_at(address)
    digest = hashlib.sha256()
    for path in sorted(set(parent_files) | set(own_files)):
        old = parent_files.get(path)
        new = own_files.get(path)
        if old == new:
            continue
        digest.update(path.encode())
        digest.update(b"|old|")
        digest.update(old or b"<absent>")
        digest.update(b"|new|")
        digest.update(new or b"<absent>")
    return digest.hexdigest()[:20]


def cherry_report(
    repo: Repo, branch_tip: str, upstream_tip: str
) -> dict[str, list[str]]:
    upstream_only = repo.graph.ancestors(
        upstream_tip
    ) - repo.graph.ancestors(branch_tip)
    branch_only = repo.graph.ancestors(
        branch_tip
    ) - repo.graph.ancestors(upstream_tip)
    upstream_ids = set()
    for address in upstream_only:
        commit = repo.graph.get(address)
        if len(commit.parents) <= 1:
            upstream_ids.add(patch_id(repo, address))
    landed: list[str] = []
    pending: list[str] = []
    ordered = sorted(
        branch_only,
        key=lambda a: repo.graph.get(a).sequence,
    )
    for address in ordered:
        commit = repo.graph.get(address)
        if len(commit.parents) > 1:
            continue
        if patch_id(repo, address) in upstream_ids:
            landed.append(address)
        else:
            pending.append(address)
    return {"landed": landed, "pending": pending}


def narrate_cherry(
    repo: Repo, branch_tip: str, upstream_tip: str
) -> str:
    report = cherry_report(repo, branch_tip, upstream_tip)
    lines = [
        f"{len(report['landed'])} landed upstream under "
        f"other addresses, {len(report['pending'])} pending"
    ]
    for address in report["landed"]:
        lines.append(
            f"  - {address[:8]} "
            f"{repo.graph.get(address).message} (landed)"
        )
    for address in report["pending"]:
        lines.append(
            f"  + {address[:8]} "
            f"{repo.graph.get(address).message} (pending)"
        )
    return "\n".join(lines)
