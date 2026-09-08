"""File locks: for the files merge cannot save, take turns on purpose.

Merge is the reason version control scales, and it does not
work on the binary asset, the generated schema, the design
file, so those paths get the older tool, taking turns, made
explicit. A lock names its holder and its reason, because a
lock that answers who but not why teaches people to steal
early, and a second lock on the same path is refused with
both facts quoted. The steal exists for the vacation
problem and is priced like the freeze override: loud, in
capitals, recording both parties, since a quiet steal is
indistinguishable from the lock never working, and the
stolen-from deserves to find their name in the journal
rather than their work in the bin. The landing check is
where the locks earn rent: a push touching a locked path
by anyone but the holder bounces with the holder named,
which turns the worst case from two lost days of work into
one short conversation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Conflict, Invalid, Missing


@dataclass(frozen=True)
class Lock:
    path: str
    holder: str
    reason: str


@dataclass
class LockOffice:
    locks: dict[str, Lock] = field(default_factory=dict)
    journal: list[str] = field(default_factory=list)

    def take(
        self, path: str, holder: str, reason: str
    ) -> str:
        if not reason.strip():
            raise Invalid(
                "a lock that answers who but not why "
                "teaches people to steal early"
            )
        standing = self.locks.get(path)
        if standing is not None:
            raise Conflict(
                f"{path} is held by {standing.holder} "
                f"({standing.reason}); ask them, or "
                "steal loudly and answer for it"
            )
        self.locks[path] = Lock(
            path=path, holder=holder, reason=reason
        )
        self.journal.append(
            f"locked: {path} by {holder} ({reason})"
        )
        return f"{path} locked by {holder}: {reason}"

    def release(self, path: str, holder: str) -> str:
        standing = self.locks.get(path)
        if standing is None:
            raise Missing(f"{path} is not locked")
        if standing.holder != holder:
            raise Invalid(
                f"{path} is held by {standing.holder}, "
                f"not {holder}; releasing someone "
                "else's lock is a steal wearing "
                "politeness"
            )
        del self.locks[path]
        self.journal.append(
            f"released: {path} by {holder}"
        )
        return f"{path} released; the turn is over"

    def steal(
        self, path: str, thief: str, why: str
    ) -> str:
        standing = self.locks.get(path)
        if standing is None:
            raise Missing(
                f"{path} is not locked; taking the "
                "unheld is just taking"
            )
        if not why.strip():
            raise Invalid(
                "a steal without a why is a quiet "
                "steal, and a quiet steal is "
                "indistinguishable from the lock "
                "never working"
            )
        entry = (
            f"STOLEN: {path} from {standing.holder} "
            f"by {thief} because {why}"
        )
        self.locks[path] = Lock(
            path=path, holder=thief, reason=why
        )
        self.journal.append(entry)
        return entry

    def check_landing(
        self, who: str, touched_paths: list[str]
    ) -> str:
        blocked = []
        for path in sorted(touched_paths):
            standing = self.locks.get(path)
            if standing and standing.holder != who:
                blocked.append(
                    f"  {path}: held by "
                    f"{standing.holder} "
                    f"({standing.reason})"
                )
        if blocked:
            raise Conflict(
                f"{who} touches {len(blocked)} locked "
                "path(s); one short conversation beats "
                "two lost days:\n"
                + "\n".join(blocked)
            )
        return (
            f"{who} touches no locked paths; land away"
        )

    def listing(self) -> str:
        if not self.locks:
            return (
                "no locks held; everything merges or "
                "nobody is editing the unmergeable"
            )
        lines = [f"{len(self.locks)} lock(s) held:"]
        for path in sorted(self.locks):
            lock = self.locks[path]
            lines.append(
                f"  {path}: {lock.holder} "
                f"({lock.reason})"
            )
        return "\n".join(lines)
