"""Code owners: every path answers to somebody, and the file says whom.

Review routing by guesswork sends the storage change to
whoever merged last, and the owners file replaces the
guesswork: patterns map path prefixes and globs to owner
teams, later rules override earlier ones so specific teams
can carve exceptions out of broad claims, and a change set
routes to the union of owners across its touched paths. The
audit is the half that keeps the file true: paths in the
tree that no rule claims are orphans listed for adoption,
and rules that match nothing in the tree are dead weight
listed for deletion, because an owners file that drifts from
the tree routes reviews with the confidence of a map drawn
for a different city. The default owner is refused as a
concept: a rule claiming everything means the file says
nothing.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field

from keel.errors import Invalid


@dataclass(frozen=True)
class OwnerRule:
    position: int
    pattern: str
    owners: tuple[str, ...]

    def matches(self, path: str) -> bool:
        if self.pattern.endswith("/"):
            return path.startswith(self.pattern)
        return fnmatch.fnmatch(path, self.pattern)


@dataclass
class OwnersFile:
    rules: list[OwnerRule] = field(default_factory=list)

    @classmethod
    def parse(cls, text: str) -> OwnersFile:
        rules: list[OwnerRule] = []
        for position, raw in enumerate(
            text.splitlines(), start=1
        ):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                raise Invalid(
                    f"line {position}: a pattern with no "
                    "owner claims nothing"
                )
            pattern = parts[0]
            if pattern in ("*", "**", "**/*"):
                raise Invalid(
                    f"line {position}: a rule claiming "
                    "everything means the file says nothing"
                )
            rules.append(
                OwnerRule(
                    position=position,
                    pattern=pattern,
                    owners=tuple(parts[1:]),
                )
            )
        return cls(rules=rules)

    def owners_of(self, path: str) -> tuple[str, ...]:
        claimed: tuple[str, ...] = ()
        for rule in self.rules:
            if rule.matches(path):
                claimed = rule.owners
        return claimed

    def route(
        self, touched_paths: list[str]
    ) -> dict[str, tuple[str, ...]]:
        reviewers: set[str] = set()
        unclaimed: list[str] = []
        for path in touched_paths:
            owners = self.owners_of(path)
            if owners:
                reviewers.update(owners)
            else:
                unclaimed.append(path)
        return {
            "reviewers": tuple(sorted(reviewers)),
            "unclaimed": tuple(sorted(unclaimed)),
        }

    def audit(self, tree_paths: list[str]) -> str:
        orphans = sorted(
            path
            for path in tree_paths
            if not self.owners_of(path)
        )
        dead = sorted(
            f"line {rule.position} ({rule.pattern})"
            for rule in self.rules
            if not any(
                rule.matches(path) for path in tree_paths
            )
        )
        lines = [
            f"{len(orphans)} orphan(s) for adoption, "
            f"{len(dead)} dead rule(s) for deletion"
        ]
        lines.extend(f"  orphan: {path}" for path in orphans)
        lines.extend(f"  dead: {rule}" for rule in dead)
        if orphans or dead:
            lines.append(
                "an owners file that drifts from the tree "
                "routes reviews with the confidence of a map "
                "drawn for a different city"
            )
        return "\n".join(lines)
