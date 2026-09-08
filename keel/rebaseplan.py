"""The rebase plan: interactive rebase with the interaction written down.

The todo list is a small program over history, and this
module runs it like one: parse, validate, execute, report.
Validation carries the rule interactive tools get wrong by
being polite: a commit that simply vanishes from the plan is
a drop nobody typed, and it is refused rather than honored,
because losing work to a deleted line is the oldest rebase
accident there is. Squash folds a commit into its
predecessor and concatenates both messages, since the fold
that keeps only one message decides silently which half of
the work stops being history. Reordering is allowed but
checked change by change: each replayed commit must find the
content its diff expects underneath it, and a step that
lands on content it never knew raises a conflict naming both
commits instead of quietly weaving them, because a rebase
that guesses at interleaving is a merge without a base. A
step whose every change was already applied by earlier steps
evaporates with a note, the same honesty the filter gives.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.commits import Commit
from keel.errors import Conflict, Invalid, Missing
from keel.repo import Repo

VERBS = ("pick", "drop", "squash", "fixup", "reword")


@dataclass(frozen=True)
class Step:
    verb: str
    prefix: str
    argument: str


@dataclass(frozen=True)
class PlanEntry:
    old_address: str
    verb: str
    new_address: str | None
    note: str

    def line(self) -> str:
        landed = (
            self.new_address[:8]
            if self.new_address
            else "gone"
        )
        return (
            f"  {self.verb} {self.old_address[:8]} -> "
            f"{landed} ({self.note})"
        )


@dataclass(frozen=True)
class PlanResult:
    entries: tuple[PlanEntry, ...]
    new_tip: str

    def narrate(self) -> str:
        landed = sum(
            1
            for entry in self.entries
            if entry.new_address is not None
        )
        lines = [
            f"plan executed: {landed} commit(s) landed, "
            f"{len(self.entries) - landed} gone"
        ]
        lines.extend(entry.line() for entry in self.entries)
        lines.append(f"new tip {self.new_tip[:8]}")
        return "\n".join(lines)


def _range_of(
    repo: Repo, base: str, tip: str
) -> list[Commit]:
    chain: list[Commit] = []
    address = tip
    while address != base:
        commit = repo.graph.get(address)
        if len(commit.parents) != 1:
            raise Invalid(
                f"{address[:8]} does not sit on a single "
                "line above the base; plans replay linear "
                "history only"
            )
        chain.append(commit)
        address = commit.parents[0]
    return list(reversed(chain))


def plan_range(repo: Repo, base: str, tip: str) -> str:
    lines = [
        f"pick {commit.address[:8]} "
        f"{commit.message.splitlines()[0]}"
        for commit in _range_of(repo, base, tip)
    ]
    return "\n".join(lines)


def parse_plan(text: str) -> list[Step]:
    steps: list[Step] = []
    for number, raw in enumerate(
        text.splitlines(), start=1
    ):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 2:
            raise Invalid(
                f"plan line {number}: a verb needs a commit"
            )
        verb, prefix = parts[0], parts[1]
        argument = parts[2] if len(parts) > 2 else ""
        if verb not in VERBS:
            raise Invalid(
                f"plan line {number}: {verb!r} is not a "
                f"verb here; the verbs are "
                f"{', '.join(VERBS)}"
            )
        if verb == "reword" and not argument.strip():
            raise Invalid(
                f"plan line {number}: reword without the "
                "new words is just a pick with suspense"
            )
        steps.append(
            Step(verb=verb, prefix=prefix, argument=argument)
        )
    if not steps:
        raise Invalid("an empty plan rebases nothing")
    return steps


def _changes_of(
    repo: Repo, commit: Commit
) -> dict[str, bytes | None]:
    current = repo.files_at(commit.address)
    parent = repo.files_at(commit.parents[0])
    changed: dict[str, bytes | None] = {}
    for path, content in current.items():
        if parent.get(path) != content:
            changed[path] = content
    for path in parent:
        if path not in current:
            changed[path] = None
    return changed


def _bind(
    repo: Repo, base: str, tip: str, plan_text: str
) -> list[tuple[Step, Commit]]:
    chain = _range_of(repo, base, tip)
    by_prefix = {
        commit.address[:8]: commit for commit in chain
    }
    named: list[tuple[Step, Commit]] = []
    for step in parse_plan(plan_text):
        commit = by_prefix.get(step.prefix)
        if commit is None:
            raise Missing(
                f"{step.prefix} is not in the range being "
                "replanned"
            )
        named.append((step, commit))
    planned = {commit.address for _, commit in named}
    for commit in chain:
        if commit.address not in planned:
            raise Invalid(
                f"{commit.address[:8]} "
                f"({commit.message.splitlines()[0]!r}) is "
                "missing from the plan; a commit that "
                "vanishes from the todo is a drop nobody "
                "typed, so type the drop"
            )
    if named and named[0][0].verb in ("squash", "fixup"):
        raise Invalid(
            f"the first step cannot {named[0][0].verb}; "
            "there is no predecessor to fold into"
        )
    return named


def _replay(
    repo: Repo, commit: Commit, files: dict[str, bytes]
) -> int:
    changes = _changes_of(repo, commit)
    parent_files = repo.files_at(commit.parents[0])
    applied = 0
    for path, content in changes.items():
        expected = parent_files.get(path)
        held = files.get(path)
        if held == content:
            continue
        if held != expected:
            raise Conflict(
                f"{commit.address[:8]} expected {path} as "
                "its parent left it, but the plan reordered "
                "it onto different content; a rebase that "
                "guesses at interleaving is a merge without "
                "a base"
            )
        if content is None:
            files.pop(path, None)
        else:
            files[path] = content
        applied += 1
    return applied


def execute(
    repo: Repo,
    base: str,
    tip: str,
    plan_text: str,
    branch: str | None = None,
) -> PlanResult:
    named = _bind(repo, base, tip, plan_text)
    pending: list[tuple[dict[str, bytes], str, list[str]]] = []
    files = dict(repo.files_at(base))
    entries_meta: list[tuple[str, str]] = []
    for step, commit in named:
        if step.verb == "drop":
            entries_meta.append(
                (commit.address, "dropped as written")
            )
            continue
        applied = _replay(repo, commit, files)
        if applied == 0 and step.verb not in (
            "squash",
            "fixup",
        ):
            entries_meta.append(
                (
                    commit.address,
                    "evaporated; every change was already "
                    "in place",
                )
            )
            continue
        if step.verb in ("squash", "fixup"):
            if not pending:
                raise Invalid(
                    f"{step.verb} found no landed "
                    "predecessor to fold into"
                )
            _, kept_message, folded = pending[-1]
            message = (
                kept_message
                if step.verb == "fixup"
                else kept_message + "\n\n" + commit.message
            )
            pending[-1] = (
                dict(files),
                message,
                [*folded, commit.address],
            )
            note = (
                "folded silently; fixup messages are "
                "noise by definition"
                if step.verb == "fixup"
                else "folded into predecessor"
            )
            entries_meta.append((commit.address, note))
            continue
        message = (
            step.argument
            if step.verb == "reword"
            else commit.message
        )
        note = (
            "reworded"
            if step.verb == "reword"
            else "picked"
        )
        pending.append(
            (dict(files), message, [commit.address])
        )
        entries_meta.append((commit.address, note))

    if not pending:
        raise Invalid(
            "the plan landed nothing; a rebase to an empty "
            "range is a branch deletion wearing a todo"
        )
    landed_by_old: dict[str, str] = {}
    previous = base
    for snapshot, message, members in pending:
        created = repo.commit_with_parents(
            snapshot, message, (previous,)
        )
        previous = created.address
        for member in members:
            landed_by_old[member] = created.address
    if branch is not None:
        repo.refs.create_branch(branch, previous)
    entries = tuple(
        PlanEntry(
            old_address=old,
            verb=next(
                step.verb
                for step, commit in named
                if commit.address == old
            ),
            new_address=landed_by_old.get(old),
            note=note,
        )
        for old, note in entries_meta
    )
    return PlanResult(entries=entries, new_tip=previous)
