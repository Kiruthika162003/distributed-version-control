"""The stage: a place to compose the commit you mean, not the mess you have.

The working copy is where work happens and work is messy; the
stage is the draft of the next commit, built path by path, so
a commit can say one thing even when the directory says
three. Status is therefore a three-way comparison with
precise vocabulary: staged changes are the diff from HEAD to
stage, unstaged changes are the diff from stage to working
copy, and untracked files are in neither, and the three
categories never blur because each answers a different
question: what will commit, what could, and what is invisible
to history. Staging a deletion is explicit, not inferred from
absence, because a file missing from the working copy is
usually an editor buffer or a mistake, and inferring
deletions from absence is how version control systems delete
work during lunch.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing
from keel.repo import Repo


@dataclass
class Stage:
    repo: Repo
    entries: dict[str, bytes] = field(default_factory=dict)
    deletions: set[str] = field(default_factory=set)

    def _head_files(self) -> dict[str, bytes]:
        if not self.repo.refs.branches:
            return {}
        return self.repo.head_files()

    def add(self, path: str, content: bytes) -> str:
        self.deletions.discard(path)
        self.entries[path] = content
        return f"{path} staged"

    def stage_deletion(self, path: str) -> str:
        head = self._head_files()
        if path not in head and path not in self.entries:
            raise Missing(
                f"{path} is not in HEAD or the stage; there "
                "is nothing to delete"
            )
        self.entries.pop(path, None)
        self.deletions.add(path)
        return (
            f"{path} staged for deletion; deletions are said, "
            "never inferred from absence"
        )

    def unstage(self, path: str) -> str:
        if (
            path not in self.entries
            and path not in self.deletions
        ):
            raise Missing(f"{path} is not staged")
        self.entries.pop(path, None)
        self.deletions.discard(path)
        return f"{path} unstaged; the working copy is untouched"

    def next_snapshot(self) -> dict[str, bytes]:
        files = dict(self._head_files())
        for path in self.deletions:
            files.pop(path, None)
        files.update(self.entries)
        return files

    def status(
        self, working: dict[str, bytes]
    ) -> dict[str, list[str]]:
        head = self._head_files()
        staged_view = self.next_snapshot()
        staged: list[str] = []
        for path in sorted(set(head) | set(staged_view)):
            if head.get(path) != staged_view.get(path):
                verb = (
                    "deleted"
                    if path not in staged_view
                    else (
                        "added"
                        if path not in head
                        else "modified"
                    )
                )
                staged.append(f"{path} ({verb})")
        unstaged: list[str] = []
        for path in sorted(staged_view):
            if (
                path in working
                and working[path] != staged_view[path]
            ):
                unstaged.append(path)
        untracked = sorted(
            path
            for path in working
            if path not in staged_view and path not in head
        )
        return {
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
        }

    def commit(self, message: str):
        if not self.entries and not self.deletions:
            raise Invalid(
                "the stage is empty; there is no draft to "
                "turn into a commit"
            )
        snapshot = self.next_snapshot()
        commit = self.repo.commit(snapshot, message)
        self.entries.clear()
        self.deletions.clear()
        return commit
