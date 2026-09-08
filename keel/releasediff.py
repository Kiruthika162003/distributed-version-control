"""Release diff: two sealed cuts compared as shipments, not as commits.

The changelog says what the developers did between two
releases; the release diff says what the customer receives,
and the two answers differ whenever work was reverted,
folded, or overwritten on the way. The comparison is tag to
tag because releases are the sealed things, and it reads as
a shipping manifest: files that enter the shipment, files
that leave it, files whose contents changed with the weight
of the change, and the unchanged majority counted in one
line, since a manifest that lists every untouched crate
buries the three that matter. The closing line reconciles
against the changelog's world honestly: a release where
many commits landed but little content changed is called
what it is, a lot of walking to arrive nearby, which is
sometimes refactoring's whole job and sometimes a quarter
of churn, and the number lets the reader ask which.
"""

from __future__ import annotations

from keel.repo import Repo
from keel.tags import TagStore


def manifest_diff(
    repo: Repo,
    tags: TagStore,
    old_tag: str,
    new_tag: str,
) -> str:
    old_tip = tags.resolve(old_tag)
    new_tip = tags.resolve(new_tag)
    old_files = repo.files_at(old_tip)
    new_files = repo.files_at(new_tip)
    entered = sorted(set(new_files) - set(old_files))
    left = sorted(set(old_files) - set(new_files))
    changed = sorted(
        path
        for path in set(old_files) & set(new_files)
        if old_files[path] != new_files[path]
    )
    unchanged = (
        len(set(old_files) & set(new_files))
        - len(changed)
    )
    lines = [
        f"shipment {old_tag} -> {new_tag}:"
    ]
    for path in entered:
        lines.append(
            f"  enters: {path} "
            f"({len(new_files[path])} byte(s))"
        )
    for path in left:
        lines.append(
            f"  leaves: {path}; the customer notices "
            "departures before arrivals"
        )
    for path in changed:
        delta = len(new_files[path]) - len(
            old_files[path]
        )
        sign = "+" if delta >= 0 else ""
        lines.append(
            f"  changes: {path} ({sign}{delta} "
            "byte(s))"
        )
    lines.append(
        f"  {unchanged} crate(s) untouched, counted "
        "and not listed"
    )
    commits_between = len(
        repo.graph.ancestors(new_tip)
        - repo.graph.ancestors(old_tip)
    )
    moved = len(entered) + len(left) + len(changed)
    lines.append(
        f"{commits_between} commit(s) of walking, "
        f"{moved} file(s) of arriving"
    )
    if commits_between >= moved * 3 and moved:
        lines.append(
            "a lot of walking to arrive nearby; "
            "sometimes refactoring's whole job, "
            "sometimes a quarter of churn, and the "
            "number lets you ask which"
        )
    return "\n".join(lines)
