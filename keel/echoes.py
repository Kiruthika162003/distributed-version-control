"""Echoes: commits that sum to silence, found by content, not by name.

A revert wears its name only when the tool wrote it; the
hand-made undo wears a shrug like everything else, so the
echo hunt reads content instead of subjects: for every
pair of single-parent commits on the line, the earlier
one's change set inverted and compared against the later
one's, and an exact match is an echo, two commits that
sum to silence. Echoes are reported with both subjects
and the distance between them, because the echo one
commit later is a quick correction while the echo forty
commits later is a decision unmade after everyone
adjusted to it, and those deserve different meetings. The
pair is a finding and not an error, plenty of echoes
being the right call twice, and the report says so, the
hunt's job being to make the silence visible, not to
assign the blame for it.
"""

from __future__ import annotations

from keel.repo import Repo


def _changes(
    repo: Repo, address: str
) -> dict[str, tuple[bytes | None, bytes | None]]:
    commit = repo.graph.get(address)
    current = repo.files_at(address)
    parent = (
        repo.files_at(commit.parents[0])
        if commit.parents
        else {}
    )
    return {
        path: (parent.get(path), current.get(path))
        for path in set(parent) | set(current)
        if parent.get(path) != current.get(path)
    }


def _inverts(
    earlier: dict, later: dict
) -> bool:
    if set(earlier) != set(later):
        return False
    if not earlier:
        return False
    return all(
        later[path] == (after, before)
        for path, (before, after) in earlier.items()
    )


def find_echoes(
    repo: Repo, tip: str
) -> list[tuple[str, str, int]]:
    line = [
        commit
        for commit in sorted(
            repo.graph.log(tip),
            key=lambda held: held.sequence,
        )
        if len(commit.parents) == 1
    ]
    change_sets = [
        (commit, _changes(repo, commit.address))
        for commit in line
    ]
    found = []
    for early_index, (early, early_changes) in (
        enumerate(change_sets)
    ):
        for late, late_changes in change_sets[
            early_index + 1:
        ]:
            if _inverts(early_changes, late_changes):
                found.append(
                    (
                        early.address,
                        late.address,
                        late.sequence - early.sequence,
                    )
                )
    return found


def report(repo: Repo, tip: str) -> str:
    echoes = find_echoes(repo, tip)
    if not echoes:
        return (
            "no echoes; nothing here has been "
            "unsaid"
        )
    lines = [
        f"{len(echoes)} echo(es), commits that sum "
        "to silence:"
    ]
    for early, late, distance in echoes:
        early_subject = repo.graph.get(
            early
        ).message.splitlines()[0]
        late_subject = repo.graph.get(
            late
        ).message.splitlines()[0]
        pace = (
            "a quick correction"
            if distance <= 2
            else "a decision unmade after everyone "
            "adjusted"
        )
        lines.append(
            f"  {early[:8]} ({early_subject!r}) "
            f"unsaid by {late[:8]} "
            f"({late_subject!r}), {distance} "
            f"commit(s) apart; {pace}"
        )
    lines.append(
        "findings, not errors; plenty of echoes are "
        "the right call twice, and the hunt only "
        "makes the silence visible"
    )
    return "\n".join(lines)
