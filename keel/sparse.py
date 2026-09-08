"""Sparse checkout: materialize the corner of the monorepo you actually work in.

A repository can hold forty teams' code while a developer
touches one directory, and the sparse profile makes the
working copy match the work: chosen path prefixes
materialize, everything else stays as history only, present
in commits but absent from the desk. The profile is
prefix-based and additive, widened by request, and the two
honest edges are handled by name: a commit built from a
sparse desk still snapshots the full tree, unmaterialized
paths carried through from HEAD unchanged, because a sparse
checkout that silently commits deletions of everything it
did not show is the monorepo horror story with the shortest
fuse; and reads outside the profile fail with the profile
quoted, so "file not found" never means "found, but hidden
by a setting you forgot".
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing
from keel.repo import Repo


@dataclass
class SparseDesk:
    repo: Repo
    prefixes: set[str] = field(default_factory=set)

    def widen(self, prefix: str) -> str:
        if prefix.startswith("/") or not prefix:
            raise Invalid(
                f"{prefix!r} is not a prefix; relative "
                "directories only"
            )
        clean = prefix.rstrip("/") + "/"
        self.prefixes.add(clean)
        return (
            f"profile widened to include {clean}; the "
            "profile is additive by design"
        )

    def _visible(self, path: str) -> bool:
        return any(
            path.startswith(prefix)
            for prefix in self.prefixes
        )

    def materialize(self) -> dict[str, bytes]:
        if not self.prefixes:
            raise Invalid(
                "an empty profile materializes nothing; "
                "widen it first"
            )
        full = self.repo.head_files()
        return {
            path: content
            for path, content in full.items()
            if self._visible(path)
        }

    def read(self, path: str) -> bytes:
        full = self.repo.head_files()
        if path not in full:
            raise Missing(f"{path} is not in HEAD")
        if not self._visible(path):
            raise Missing(
                f"{path} exists but is outside the sparse "
                f"profile [{', '.join(sorted(self.prefixes))}]"
                "; found-but-hidden must never read as "
                "not-found"
            )
        return full[path]

    def commit_sparse(
        self, desk_files: dict[str, bytes], message: str
    ):
        full = dict(self.repo.head_files())
        for path in list(full):
            if self._visible(path):
                del full[path]
        for path in desk_files:
            if not self._visible(path):
                raise Invalid(
                    f"{path} is outside the profile; a "
                    "sparse desk cannot speak for "
                    "directories it does not show"
                )
        full.update(desk_files)
        return self.repo.commit(full, message)

    def coverage(self) -> str:
        full = self.repo.head_files()
        shown = sum(
            1 for path in full if self._visible(path)
        )
        return (
            f"{shown} of {len(full)} file(s) on the desk; "
            "the rest is history only"
        )
