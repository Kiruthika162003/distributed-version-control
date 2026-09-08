"""The dry dock: inspections gathered into a yard list, worst first.

The health report tells you how the ship is; the dry dock
tells you what to do about it, in the order a yard actually
works. Four inspections file findings: the physical for
corruption, the merge audit for meetings that bear nothing,
the portability audit for paths that break on other
filesystems, and the twins report for content drifting
apart, and each finding is converted to a work order with a
severity the ordering respects, hull before rigging before
paint, because a yard that fixes the paint while the hull
leaks is billing hours, not repairing ships. Work orders
name the tool for the job in this workshop's own inventory,
the airlock and the expunge and the restructure by name,
since a repair plan that says fix it without saying with
what is a wish. The empty yard list is the goal state and
says so: seaworthy, no orders, the dock stands ready.
"""

from __future__ import annotations

from keel.fsck import Physical
from keel.mergeaudit import audit as merge_audit
from keel.portability import audit_paths
from keel.repo import Repo
from keel.twins import near_twins

HULL = "hull"
RIGGING = "rigging"
PAINT = "paint"
SEVERITY_ORDER = (HULL, RIGGING, PAINT)


def yard_list(repo: Repo) -> str:
    tip = repo.refs.current()
    orders: list[tuple[str, str]] = []

    physical = Physical(repo=repo).run()
    if not physical.startswith("physical clean"):
        for line in physical.splitlines()[1:]:
            orders.append(
                (
                    HULL,
                    line.strip()
                    + " -> refuse arrivals through "
                    "the airlock until repaired",
                )
            )

    _meetings, merge_findings = merge_audit(repo, tip)
    for finding in merge_findings:
        orders.append(
            (
                RIGGING,
                f"{finding.address[:8]} "
                f"[{finding.kind}] -> rewrite the "
                "line with the rebase plan if it "
                "still matters",
            )
        )

    for finding in audit_paths(
        sorted(repo.files_at(tip))
    ):
        orders.append(
            (
                RIGGING,
                finding
                + " -> move it with the restructure "
                "map",
            )
        )

    for left, right, score in near_twins(repo, tip):
        orders.append(
            (
                PAINT,
                f"{left} ~ {right} ({score:.0%}) -> "
                "pick a canonical copy and delete "
                "the drifting one",
            )
        )

    if not orders:
        return (
            "seaworthy; no orders, and the dock "
            "stands ready"
        )
    orders.sort(
        key=lambda held: SEVERITY_ORDER.index(held[0])
    )
    lines = [
        f"the yard list, {len(orders)} order(s), "
        "hull before rigging before paint:"
    ]
    lines.extend(
        f"  [{severity}] {work}"
        for severity, work in orders
    )
    lines.append(
        "a repair plan that says fix it without "
        "saying with what is a wish"
    )
    return "\n".join(lines)
