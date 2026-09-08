"""The undo advisor: the reflog read back as instructions, not archaeology.

Every recovery in this system already exists as a journal
line; what people lack at the bad moment is the translation.
The advisor reads the reflog for the two accidents that
actually happen, the deleted branch and the reset that
threw away a tip, and answers each with three parts: the
diagnosis in plain words, the exact journal line as
evidence, and a prescription that names the address to
point a branch at, because advice without the address is
sympathy. The performing methods do what the prescription
says and nothing more. The honest refusal matters as much:
when the journal holds no record of the claimed accident,
the advisor says so instead of guessing, since not every
loss is recoverable and pretending otherwise costs the
searcher the hour they needed for backups.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from keel.errors import Corrupt, Missing
from keel.repo import Repo

_DELETED = re.compile(
    r"^branch (?P<name>\S+) deleted at "
    r"(?P<prefix>[0-9a-f]{8})$"
)
_FORCED = re.compile(
    r"^branch (?P<name>\S+) force-moved "
    r"(?P<old>[0-9a-f]{8}) -> (?P<new>[0-9a-f]{8}): "
    r"(?P<reason>.*)$"
)


@dataclass(frozen=True)
class Advice:
    diagnosis: str
    evidence: str
    prescription: str

    def render(self) -> str:
        return (
            f"diagnosis:    {self.diagnosis}\n"
            f"evidence:     {self.evidence}\n"
            f"prescription: {self.prescription}"
        )


@dataclass
class UndoAdvisor:
    repo: Repo

    def _expand(self, prefix: str) -> str:
        matches = [
            address
            for address in self.repo.graph.commits
            if address.startswith(prefix)
        ]
        if len(matches) != 1:
            raise Corrupt(
                f"{prefix} matches {len(matches)} "
                "commit(s); the journal names something "
                "the graph cannot single out"
            )
        return matches[0]

    def deleted_branch(self, name: str) -> Advice:
        for entry in reversed(self.repo.refs.reflog):
            found = _DELETED.match(entry)
            if found and found.group("name") == name:
                address = self._expand(
                    found.group("prefix")
                )
                return Advice(
                    diagnosis=(
                        f"{name} was deleted, but its tip "
                        "still exists; deletion removed "
                        "the name, not the history"
                    ),
                    evidence=entry,
                    prescription=(
                        f"point a branch at {address[:8]} "
                        "and the deletion is undone"
                    ),
                )
        raise Missing(
            f"the journal holds no deletion of {name}; "
            "not every loss is recoverable, and "
            "pretending otherwise costs the hour needed "
            "for backups"
        )

    def resurrect(self, name: str) -> str:
        advice = self.deleted_branch(name)
        prefix = _DELETED.match(advice.evidence).group(
            "prefix"
        )
        address = self._expand(prefix)
        self.repo.refs.create_branch(name, address)
        return (
            f"{name} stands again at {address[:8]}; the "
            "reflog kept its word"
        )

    def reset_victim(self, branch: str) -> Advice:
        for entry in reversed(self.repo.refs.reflog):
            found = _FORCED.match(entry)
            if found and found.group("name") == branch:
                address = self._expand(found.group("old"))
                return Advice(
                    diagnosis=(
                        f"{branch} was force-moved off "
                        f"{address[:8]} "
                        f"({found.group('reason')}); the "
                        "abandoned tip is intact"
                    ),
                    evidence=entry,
                    prescription=(
                        f"branch from {address[:8]} to "
                        "hold the abandoned work before "
                        "the journal is trimmed"
                    ),
                )
        raise Missing(
            f"the journal holds no force-move of "
            f"{branch}; whatever happened, it was not a "
            "reset this repository saw"
        )

    def rescue(self, branch: str, as_name: str) -> str:
        advice = self.reset_victim(branch)
        prefix = _FORCED.match(advice.evidence).group("old")
        address = self._expand(prefix)
        self.repo.refs.create_branch(as_name, address)
        return (
            f"{as_name} holds the abandoned tip "
            f"{address[:8]}; trimmed journals can no "
            "longer take it"
        )
