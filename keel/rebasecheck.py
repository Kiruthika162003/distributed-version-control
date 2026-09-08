"""Rebase check: the move that claims to only move, held to the claim.

A rebase promises to relocate work without editing it, and
the promise is checkable in one comparison nobody bothers
to make: the tree at the old tip against the tree at the
new one. Identical trees mean the promise held to the
byte, and the check says so in those words so the force
push that follows carries a receipt instead of a mood.
Drift is not automatically a lie, a conflict resolved
mid-rebase edits content legitimately, so the check
reports rather than refuses, naming each drifted path
with its kind, edited, appeared, or vanished, because the
reviewer of a force push deserves the same courtesy as
the reviewer of a merge: told what changed, not assured
that nothing did. The commit count rides along, a rebase
that set out with five commits and arrived with three has
folded something, and folding is fine exactly when it is
not a surprise.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.repo import Repo


@dataclass(frozen=True)
class RebaseVerdict:
    clean: bool
    drifted: tuple[tuple[str, str], ...]
    commits_before: int
    commits_after: int


def verify(
    repo: Repo,
    old_tip: str,
    new_tip: str,
    base: str,
) -> RebaseVerdict:
    old_files = repo.files_at(old_tip)
    new_files = repo.files_at(new_tip)
    drifted: list[tuple[str, str]] = []
    for path in sorted(
        set(old_files) | set(new_files)
    ):
        old = old_files.get(path)
        new = new_files.get(path)
        if old == new:
            continue
        if old is None:
            drifted.append((path, "appeared"))
        elif new is None:
            drifted.append((path, "vanished"))
        else:
            drifted.append((path, "edited"))
    base_line = repo.graph.ancestors(base)
    before = len(
        repo.graph.ancestors(old_tip) - base_line
    )
    after = len(
        repo.graph.ancestors(new_tip) - base_line
    )
    return RebaseVerdict(
        clean=not drifted,
        drifted=tuple(drifted),
        commits_before=before,
        commits_after=after,
    )


def narrate(
    repo: Repo,
    old_tip: str,
    new_tip: str,
    base: str,
) -> str:
    verdict = verify(repo, old_tip, new_tip, base)
    lines = []
    if verdict.clean:
        lines.append(
            "content preserved to the byte; the "
            "rebase moved and did nothing else, and "
            "the force push that follows carries a "
            "receipt instead of a mood"
        )
    else:
        lines.append(
            f"{len(verdict.drifted)} path(s) drifted; "
            "told what changed, not assured that "
            "nothing did:"
        )
        lines.extend(
            f"  {path}: {kind}"
            for path, kind in verdict.drifted
        )
    lines.append(
        f"commits: {verdict.commits_before} before, "
        f"{verdict.commits_after} after"
    )
    if verdict.commits_after < verdict.commits_before:
        lines.append(
            "something folded on the way; folding is "
            "fine exactly when it is not a surprise"
        )
    return "\n".join(lines)
