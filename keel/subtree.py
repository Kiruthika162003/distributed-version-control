"""Subtrees: vendoring with receipts, not adoption papers lost in a drawer.

Copying another project into a directory is easy; knowing
which of its commits you copied, three months later with a
security patch pending, is the part teams lose. The ledger
keeps each graft's prefix paired with the guest tip it last
synced, so a pull knows exactly what changed upstream and
applies only that, and the receipt names both addresses,
because a vendored directory without its source address is
an orphan with a job. Pulls respect local reality: a
vendored file the host has edited is a fork whether anyone
admits it or not, and pulling upstream over it would erase
the fork silently, so the collision is refused with the path
named and the human chooses. The split hands the directory
back as plain files, the reverse door kept oiled, since
vendoring that cannot be undone is not vendoring but
absorption.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Conflict, Invalid, Missing
from keel.repo import Repo


@dataclass
class SubtreeLedger:
    host: Repo
    grafts: dict[str, str] = field(default_factory=dict)

    def _check_prefix(self, prefix: str) -> None:
        if not prefix.endswith("/") or prefix == "/":
            raise Invalid(
                f"{prefix!r} is not a graft point; a "
                "prefix is a directory and ends with a "
                "slash"
            )
        for held in self.grafts:
            if held.startswith(prefix) or prefix.startswith(
                held
            ):
                raise Invalid(
                    f"{prefix} overlaps the graft at "
                    f"{held}; nested vendoring is an "
                    "org chart, not a tree"
                )

    def add(self, guest: Repo, prefix: str) -> str:
        self._check_prefix(prefix)
        host_files = self.host.head_files()
        squatters = [
            path
            for path in host_files
            if path.startswith(prefix)
        ]
        if squatters:
            raise Invalid(
                f"{len(squatters)} file(s) already live "
                f"under {prefix}; a graft onto occupied "
                "ground buries somebody's work"
            )
        guest_tip = guest.refs.current()
        vendored = {
            prefix + path: content
            for path, content in guest.head_files().items()
        }
        self.host.commit(
            {**host_files, **vendored},
            f"vendor {prefix} from {guest_tip[:8]}",
        )
        self.grafts[prefix] = guest_tip
        return (
            f"grafted {len(vendored)} file(s) under "
            f"{prefix}, sourced at {guest_tip[:8]}"
        )

    def pull(self, guest: Repo, prefix: str) -> str:
        recorded = self.grafts.get(prefix)
        if recorded is None:
            raise Missing(
                f"{prefix} was never grafted; pull has "
                "nothing to continue"
            )
        guest_tip = guest.refs.current()
        if guest_tip == recorded:
            return (
                f"{prefix} is current with {guest_tip[:8]}; "
                "nothing upstream moved"
            )
        old_files = guest.files_at(recorded)
        new_files = guest.files_at(guest_tip)
        host_files = dict(self.host.head_files())
        applied = 0
        for path in sorted(set(old_files) | set(new_files)):
            old = old_files.get(path)
            new = new_files.get(path)
            if old == new:
                continue
            host_path = prefix + path
            held = host_files.get(host_path)
            if held == new:
                continue
            if held != old:
                raise Conflict(
                    f"{host_path} was edited locally since "
                    f"the graft at {recorded[:8]}; this is "
                    "a fork whether anyone admits it or "
                    "not, and pulling over it would erase "
                    "the fork silently"
                )
            if new is None:
                host_files.pop(host_path, None)
            else:
                host_files[host_path] = new
            applied += 1
        self.host.commit(
            host_files,
            f"pull {prefix}: {recorded[:8]} -> "
            f"{guest_tip[:8]}",
        )
        self.grafts[prefix] = guest_tip
        return (
            f"pulled {applied} change(s) into {prefix}: "
            f"{recorded[:8]} -> {guest_tip[:8]}"
        )

    def split(
        self, prefix: str
    ) -> tuple[dict[str, bytes], str]:
        recorded = self.grafts.get(prefix)
        if recorded is None:
            raise Missing(
                f"{prefix} was never grafted; there is "
                "nothing to hand back"
            )
        stripped = {
            path[len(prefix):]: content
            for path, content in (
                self.host.head_files().items()
            )
            if path.startswith(prefix)
        }
        return stripped, (
            f"split {len(stripped)} file(s) out of "
            f"{prefix}, last synced at {recorded[:8]}; "
            "the reverse door stays oiled"
        )
