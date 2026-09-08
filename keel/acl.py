"""Write access: who may land where, decided by roster, explained by name.

Ownership routing says who reviews; access says who may
land at all, and the two are kept separate because plenty
of paths welcome anyone's patch under anyone's review while
a few, the deploy scripts, the signing keys, the pricing
table, welcome only their keepers. Only granted paths are
governed: the table guards what someone bothered to guard,
and everything else stays open, since a default-closed
repository teaches people to work in forks and merge
strangers. Denials do the explaining that makes access
control tolerable: each denied path names the teams whose
membership would have sufficed, because "ask to join
team-infra" is an afternoon while "permission denied" is a
week of asking around. Grants name teams, never
individuals, so access survives people changing jobs
without anyone editing rules at midnight.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field

from keel.errors import Invalid, Missing


@dataclass
class AccessTable:
    teams: dict[str, set[str]] = field(
        default_factory=dict
    )
    grants: list[tuple[str, str]] = field(
        default_factory=list
    )

    def enroll(self, team: str, member: str) -> str:
        roster = self.teams.setdefault(team, set())
        if member in roster:
            raise Invalid(
                f"{member} is already on {team}; "
                "double enrollment counts nobody twice"
            )
        roster.add(member)
        return f"{member} joins {team}"

    def retire(self, team: str, member: str) -> str:
        roster = self.teams.get(team, set())
        if member not in roster:
            raise Missing(
                f"{member} is not on {team}"
            )
        roster.remove(member)
        return (
            f"{member} leaves {team}; the grants "
            "never mentioned them, so nothing else "
            "changes"
        )

    def grant(self, pattern: str, team: str) -> str:
        if team not in self.teams:
            raise Missing(
                f"{team} has no roster; grant to teams "
                "that exist, never to individuals, so "
                "access survives people changing jobs"
            )
        self.grants.append((pattern, team))
        return f"{pattern} guarded by {team}"

    def _guards(self, path: str) -> list[str]:
        found = []
        for pattern, team in self.grants:
            if pattern.endswith("/"):
                if path.startswith(pattern):
                    found.append(team)
            elif fnmatch.fnmatch(path, pattern):
                found.append(team)
        return found

    def may_write(self, who: str, path: str) -> bool:
        guards = self._guards(path)
        if not guards:
            return True
        return any(
            who in self.teams.get(team, set())
            for team in guards
        )

    def check(
        self, who: str, touched_paths: list[str]
    ) -> str:
        denied: list[str] = []
        for path in sorted(touched_paths):
            if self.may_write(who, path):
                continue
            teams = ", ".join(
                sorted(set(self._guards(path)))
            )
            denied.append(
                f"  {path}: membership in {teams} "
                "would have sufficed"
            )
        if denied:
            raise Invalid(
                f"{who} denied on {len(denied)} "
                "path(s); asking to join a team is an "
                "afternoon, permission denied is a "
                "week:\n" + "\n".join(denied)
            )
        return (
            f"{who} may land all "
            f"{len(touched_paths)} path(s)"
        )

    def report(self) -> str:
        lines = [
            f"{len(self.teams)} team(s), "
            f"{len(self.grants)} grant(s):"
        ]
        for team in sorted(self.teams):
            roster = ", ".join(
                sorted(self.teams[team])
            )
            lines.append(
                f"  {team}: {roster or 'empty roster'}"
            )
        for pattern, team in self.grants:
            lines.append(
                f"  {pattern} guarded by {team}"
            )
        lines.append(
            "everything unmentioned stays open; a "
            "default-closed repository teaches people "
            "to work in forks"
        )
        return "\n".join(lines)
