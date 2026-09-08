"""Portability: the tree audited against the filesystems it will meet.

A repository lives longer than any one machine, and the
paths that work here can break there in three known ways.
Case collisions first: App.py and app.py are two files on
one filesystem and one file on another, so the checkout
that merges them silently loses somebody's work, which is
why the collision is an error here and a mystery ticket
everywhere else. Reserved names second: a directory named
con or aux checks out nowhere on Windows, and the name
that cannot exist on a contributor's machine is a
contributor lost quietly. Length third, flagged at a
threshold with the threshold stated, because deep trees
plus long names plus a checkout prefix overflow limits
that nobody budgets for until the error message arrives
truncated. The audit reports all three families at once,
one trip, and a clean tree is told it travels well, since
a report that only speaks of trouble is opened only in
trouble.
"""

from __future__ import annotations

from keel.repo import Repo

RESERVED = (
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "com2",
    "lpt1",
    "lpt2",
)
LENGTH_LIMIT = 180


def audit_paths(paths: list[str]) -> list[str]:
    findings: list[str] = []
    by_folded: dict[str, list[str]] = {}
    for path in paths:
        by_folded.setdefault(
            path.lower(), []
        ).append(path)
    for folded in sorted(by_folded):
        held = by_folded[folded]
        if len(held) > 1:
            findings.append(
                "case collision: "
                + " and ".join(sorted(held))
                + " are two files here and one file "
                "on a case-folding filesystem; the "
                "checkout that merges them loses "
                "somebody's work"
            )
    for path in sorted(paths):
        for segment in path.split("/"):
            base = segment.split(".")[0].lower()
            if base in RESERVED:
                findings.append(
                    f"reserved name: {path} contains "
                    f"{segment!r}, which cannot exist "
                    "on Windows; a name that cannot "
                    "check out is a contributor lost "
                    "quietly"
                )
                break
    for path in sorted(paths):
        if len(path) > LENGTH_LIMIT:
            findings.append(
                f"long path: {path[:40]}... runs "
                f"{len(path)} character(s) against "
                f"the budget of {LENGTH_LIMIT}; "
                "checkout prefixes eat the rest"
            )
    return findings


def audit(repo: Repo, address: str) -> str:
    paths = sorted(repo.files_at(address))
    findings = audit_paths(paths)
    if not findings:
        return (
            f"{len(paths)} path(s) audited; this tree "
            "travels well"
        )
    lines = [
        f"{len(findings)} portability finding(s) in "
        f"{len(paths)} path(s), all three families "
        "checked in one trip:"
    ]
    lines.extend(f"  {finding}" for finding in findings)
    return "\n".join(lines)
