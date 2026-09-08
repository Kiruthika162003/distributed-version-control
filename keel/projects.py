"""Projects: a monorepo is several repositories agreeing to share a graph.

The history is one graph but the questions are per-project,
and the atlas maps prefixes to project names so the
questions can be asked precisely: which projects does this
commit touch, what is one project's own log, and which
projects need their checks run for a given landing, the
question selective CI asks a hundred times a day. Prefixes
must not nest, because a file that belongs to two projects
makes every per-project answer a lie in one direction or
the other, and files outside every prefix are billed to the
commons, named as such, since a monorepo's unclaimed floor
space is real and pretending it belongs to someone hides
who sweeps it. The touch report says commons out loud for
the same reason the owners file lists orphans: what has no
name gets no checks, and what gets no checks gets the
outage.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.commits import Commit
from keel.errors import Invalid, Missing
from keel.repo import Repo

COMMONS = "commons"


@dataclass
class Atlas:
    projects: dict[str, str] = field(default_factory=dict)

    def claim(self, name: str, prefix: str) -> str:
        if not prefix.endswith("/"):
            raise Invalid(
                f"{prefix!r} is not a prefix; projects "
                "own directories, and directories end "
                "with a slash"
            )
        if name == COMMONS:
            raise Invalid(
                "commons is the name of the unclaimed "
                "floor; claiming it hides who sweeps"
            )
        if name in self.projects:
            raise Invalid(f"{name} already claims "
                          f"{self.projects[name]}")
        for held_name, held in self.projects.items():
            if held.startswith(prefix) or (
                prefix.startswith(held)
            ):
                raise Invalid(
                    f"{prefix} nests with {held} "
                    f"({held_name}); a file with two "
                    "projects makes every per-project "
                    "answer a lie in one direction"
                )
        self.projects[name] = prefix
        return f"{name} claims {prefix}"

    def project_of(self, path: str) -> str:
        for name, prefix in self.projects.items():
            if path.startswith(prefix):
                return name
        return COMMONS

    def _touched(
        self, repo: Repo, commit: Commit
    ) -> set[str]:
        current = repo.files_at(commit.address)
        if commit.parents:
            parent = repo.files_at(commit.parents[0])
        else:
            parent = {}
        return {
            self.project_of(path)
            for path in set(current) | set(parent)
            if current.get(path) != parent.get(path)
        }

    def touches(self, repo: Repo, address: str) -> str:
        commit = repo.graph.get(address)
        touched = sorted(self._touched(repo, commit))
        return (
            f"{address[:8]} touches "
            + ", ".join(touched)
            + (
                "; the commons gets no checks, and "
                "what gets no checks gets the outage"
                if COMMONS in touched
                else ""
            )
        )

    def project_log(
        self, repo: Repo, tip: str, name: str
    ) -> list[Commit]:
        if name != COMMONS and name not in self.projects:
            raise Missing(
                f"{name} is not on the atlas; the "
                f"projects are "
                f"{', '.join(sorted(self.projects))}"
            )
        return [
            commit
            for commit in repo.graph.log(tip)
            if name in self._touched(repo, commit)
        ]

    def checks_for(
        self, repo: Repo, address: str
    ) -> list[str]:
        commit = repo.graph.get(address)
        return sorted(self._touched(repo, commit))

    def floor_plan(self, repo: Repo, tip: str) -> str:
        files = repo.files_at(tip)
        counts: dict[str, int] = {}
        for path in files:
            owner = self.project_of(path)
            counts[owner] = counts.get(owner, 0) + 1
        lines = [
            f"{len(self.projects)} project(s), "
            f"{len(files)} file(s):"
        ]
        for name in sorted(counts):
            lines.append(
                f"  {name}: {counts[name]} file(s)"
            )
        if counts.get(COMMONS):
            lines.append(
                "the commons is real floor space; "
                "somebody sweeps it or nobody does"
            )
        return "\n".join(lines)
