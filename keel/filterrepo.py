"""History filtering: rewriting the past on purpose, with a receipt.

Most of this system treats history as untouchable, and this
module is the licensed exception: filter a linear history
down to the paths that matter, or expunge a file that should
never have been committed, and get back a rewrite where every
surviving commit carries its old message atop a new address.
The receipt is the point. Because parents are part of the
digested bytes, changing one ancestor changes every address
downstream, so the report maps old addresses to new ones and
lists the commits that evaporated because nothing of theirs
survived the filter, since a rewrite without a map strands
every ticket, bookmark, and memory that referenced the old
names. Merge commits are refused rather than approximated:
filtering walks a straight line, and a merge filtered wrong
silently resurrects the very content being removed. The
expunge narration ends with the only honest advice about
leaked secrets: the rewrite removes the file from the future,
not from anyone who already fetched the past, so rotate the
secret before celebrating.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from keel.commits import Commit
from keel.errors import Invalid, Missing
from keel.repo import Repo


@dataclass(frozen=True)
class RewriteEntry:
    old_address: str
    new_address: str | None
    message: str

    def line(self) -> str:
        if self.new_address is None:
            return (
                f"  {self.old_address[:8]} dropped "
                f"({self.message})"
            )
        return (
            f"  {self.old_address[:8]} -> "
            f"{self.new_address[:8]} ({self.message})"
        )


@dataclass(frozen=True)
class FilterReport:
    entries: tuple[RewriteEntry, ...]
    new_tip: str | None

    def mapping(self) -> dict[str, str]:
        return {
            entry.old_address: entry.new_address
            for entry in self.entries
            if entry.new_address is not None
        }

    def dropped(self) -> tuple[str, ...]:
        return tuple(
            entry.old_address
            for entry in self.entries
            if entry.new_address is None
        )

    def narrate(self) -> str:
        rewritten = len(self.mapping())
        gone = len(self.dropped())
        lines = [
            f"{rewritten} commit(s) rewritten, "
            f"{gone} evaporated"
        ]
        lines.extend(entry.line() for entry in self.entries)
        if self.new_tip is None:
            lines.append(
                "nothing survived the filter; there is no "
                "new history to point at"
            )
        else:
            lines.append(
                f"new tip {self.new_tip[:8]}; every old "
                "address is now a name for something that "
                "no longer exists"
            )
        return "\n".join(lines)


@dataclass(frozen=True)
class Expunction:
    path: str
    appearances: int
    report: FilterReport

    def narrate(self) -> str:
        lines = [
            f"{self.path} appeared in {self.appearances} "
            f"of {len(self.report.entries)} commit(s)",
            f"{len(self.report.dropped())} commit(s) "
            "evaporated with it",
            "the rewrite removes the file from the future, "
            "not from anyone who already fetched the past; "
            "rotate the secret before celebrating",
        ]
        return "\n".join(lines)


def _linear_chain(repo: Repo, tip: str) -> list[Commit]:
    chain: list[Commit] = []
    address = tip
    while True:
        commit = repo.graph.get(address)
        if len(commit.parents) > 1:
            raise Invalid(
                f"{commit.address[:8]} is a merge; filtering "
                "walks a straight line, and a merge filtered "
                "wrong silently resurrects the content being "
                "removed"
            )
        chain.append(commit)
        if not commit.parents:
            return list(reversed(chain))
        address = commit.parents[0]


def filter_history(
    repo: Repo,
    tip: str,
    keep: Callable[[str], bool],
    branch: str | None = None,
) -> FilterReport:
    chain = _linear_chain(repo, tip)
    entries: list[RewriteEntry] = []
    previous_new: str | None = None
    previous_files: dict[str, bytes] = {}
    for commit in chain:
        files = repo.files_at(commit.address)
        kept = {
            path: content
            for path, content in files.items()
            if keep(path)
        }
        if kept == previous_files:
            entries.append(
                RewriteEntry(
                    old_address=commit.address,
                    new_address=None,
                    message=commit.message,
                )
            )
            continue
        parents: tuple[str, ...] = ()
        if previous_new is not None:
            parents = (previous_new,)
        rebuilt = repo.commit_with_parents(
            kept, commit.message, parents
        )
        entries.append(
            RewriteEntry(
                old_address=commit.address,
                new_address=rebuilt.address,
                message=commit.message,
            )
        )
        previous_new = rebuilt.address
        previous_files = kept
    if branch is not None and previous_new is not None:
        repo.refs.create_branch(branch, previous_new)
    return FilterReport(
        entries=tuple(entries), new_tip=previous_new
    )


def keep_prefixes(
    *prefixes: str,
) -> Callable[[str], bool]:
    def keep(path: str) -> bool:
        return any(
            path == prefix or path.startswith(prefix)
            for prefix in prefixes
        )

    return keep


def strip_paths(*paths: str) -> Callable[[str], bool]:
    doomed = set(paths)

    def keep(path: str) -> bool:
        return path not in doomed

    return keep


def expunge(
    repo: Repo,
    tip: str,
    path: str,
    branch: str | None = None,
) -> Expunction:
    chain = _linear_chain(repo, tip)
    appearances = sum(
        1
        for commit in chain
        if path in repo.files_at(commit.address)
    )
    if appearances == 0:
        raise Missing(
            f"{path} never appears in this history; an "
            "expunge that removes nothing is a story about "
            "a rewrite, not a rewrite"
        )
    report = filter_history(
        repo, tip, strip_paths(path), branch=branch
    )
    return Expunction(
        path=path, appearances=appearances, report=report
    )
