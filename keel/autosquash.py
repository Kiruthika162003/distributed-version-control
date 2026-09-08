"""Autosquash: fixup commits find their targets and jump the queue.

The workflow is honest about being a workaround: review
feedback lands as commits named fixup! plus the subject they
amend, because rewriting the branch mid-review would strand
the reviewers, and when the review closes the queue gets
reordered so every fixup sits directly behind its target.
The generator writes that plan rather than performing it,
one readable page handed to the rebase machinery, because a
tool that reorders history should show its worksheet.
Matching is by subject: a fixup! names its target's first
line, prefix matches count, and a fixup aimed at nobody is
refused with the roster of subjects it could have meant,
since silently picking the nearest commit is how amendments
land on strangers. fixup! folds and discards its own
message, noise by definition, while squash! folds and keeps
both, and the difference is the difference between fixing a
typo and merging two thoughts.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Invalid
from keel.rebaseplan import _range_of
from keel.repo import Repo

FIXUP = "fixup! "
SQUASH = "squash! "


def _subject(commit: Commit) -> str:
    return commit.message.splitlines()[0]


def _amendment(commit: Commit) -> tuple[str, str] | None:
    subject = _subject(commit)
    if subject.startswith(FIXUP):
        return "fixup", subject[len(FIXUP):]
    if subject.startswith(SQUASH):
        return "squash", subject[len(SQUASH):]
    return None


def plan(repo: Repo, base: str, tip: str) -> str:
    chain = _range_of(repo, base, tip)
    targets: list[Commit] = []
    amendments: dict[str, list[tuple[str, Commit]]] = {}
    for commit in chain:
        found = _amendment(commit)
        if found is None:
            targets.append(commit)
            continue
        verb, wanted = found
        home = None
        for candidate in targets:
            if _subject(candidate).startswith(wanted):
                home = candidate
        if home is None:
            roster = ", ".join(
                repr(_subject(candidate))
                for candidate in targets
            )
            raise Invalid(
                f"{verb}! aimed at {wanted!r} but no "
                f"target matches; the subjects on offer: "
                f"{roster or 'none'}. Silently picking "
                "the nearest commit is how amendments "
                "land on strangers"
            )
        amendments.setdefault(home.address, []).append(
            (verb, commit)
        )
    lines: list[str] = []
    for target in targets:
        lines.append(
            f"pick {target.address[:8]} "
            f"{_subject(target)}"
        )
        for verb, amendment in amendments.get(
            target.address, []
        ):
            lines.append(
                f"{verb} {amendment.address[:8]} "
                f"{_subject(amendment)}"
            )
    return "\n".join(lines)
