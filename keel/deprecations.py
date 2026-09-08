"""Deprecations: a notice with a successor, a deadline, and a spine.

A deprecation without enforcement is a suggestion, and the
ledger gives it the three parts suggestions lack. The
notice names a successor, because deprecated in favor of
nothing is an eviction without a forwarding address, and a
deadline in repository sequence numbers, the only clock
this history trusts. The audit then does what comments
cannot: it reads history and reports whether the
deprecated path has been touched since its notice, every
touch a small vote against the migration ever finishing,
and whether the deadline has passed with the path still
alive, the state that gets a name, overdue, and a louder
line, because a ledger that mumbles at deadline is a
suggestion with extra bookkeeping. Retirement closes the
notice only when the path is genuinely gone from the tip,
since celebrating a migration the tree disagrees with is
how the file comes back.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing
from keel.repo import Repo


@dataclass(frozen=True)
class Notice:
    path: str
    successor: str
    deadline: int
    noticed_at: int


@dataclass
class DeprecationLedger:
    repo: Repo
    notices: dict[str, Notice] = field(
        default_factory=dict
    )

    def declare(
        self, path: str, successor: str, deadline: int
    ) -> str:
        tip = self.repo.refs.current()
        now = self.repo.graph.get(tip).sequence
        if path not in self.repo.files_at(tip):
            raise Missing(
                f"{path} is not in the tree; "
                "deprecating a ghost frightens nobody"
            )
        if not successor.strip():
            raise Invalid(
                "deprecated in favor of nothing is an "
                "eviction without a forwarding address"
            )
        if deadline <= now:
            raise Invalid(
                f"the deadline {deadline} is not after "
                f"now ({now}); a deadline in the past "
                "is an apology in advance"
            )
        if path in self.notices:
            raise Invalid(
                f"{path} is already noticed; extend "
                "or retire, never re-declare"
            )
        self.notices[path] = Notice(
            path=path,
            successor=successor,
            deadline=deadline,
            noticed_at=now,
        )
        return (
            f"{path} deprecated in favor of "
            f"{successor}, gone by sequence {deadline}"
        )

    def _touches_since(self, notice: Notice) -> int:
        tip = self.repo.refs.current()
        count = 0
        for commit in self.repo.graph.log(tip):
            if commit.sequence <= notice.noticed_at:
                continue
            current = self.repo.files_at(commit.address)
            if commit.parents:
                parent = self.repo.files_at(
                    commit.parents[0]
                )
            else:
                parent = {}
            if current.get(notice.path) != parent.get(
                notice.path
            ):
                count += 1
        return count

    def audit(self) -> str:
        if not self.notices:
            return (
                "no notices; nothing here is dying "
                "on a schedule"
            )
        tip = self.repo.refs.current()
        now = self.repo.graph.get(tip).sequence
        files = self.repo.files_at(tip)
        lines = [f"{len(self.notices)} notice(s):"]
        for path in sorted(self.notices):
            notice = self.notices[path]
            if path not in files:
                lines.append(
                    f"  {path}: gone; retire the "
                    "notice and close the book"
                )
                continue
            touches = self._touches_since(notice)
            state = (
                "OVERDUE"
                if now > notice.deadline
                else "on schedule"
            )
            line = (
                f"  {path}: {state}, deadline "
                f"{notice.deadline}, now {now}, "
                f"{touches} touch(es) since notice"
            )
            if touches:
                line += (
                    "; every touch is a vote against "
                    "the migration finishing"
                )
            lines.append(line)
        return "\n".join(lines)

    def retire(self, path: str) -> str:
        notice = self.notices.get(path)
        if notice is None:
            raise Missing(f"{path} was never noticed")
        tip = self.repo.refs.current()
        if path in self.repo.files_at(tip):
            raise Invalid(
                f"{path} is still in the tree; "
                "celebrating a migration the tree "
                "disagrees with is how the file "
                "comes back"
            )
        del self.notices[path]
        return (
            f"{path} retired; {notice.successor} "
            "carries on"
        )
