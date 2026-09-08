"""The merge audit: every meeting in the graph asked what it accomplished.

Merges are load-bearing commits and some of them bear
nothing, so the audit walks every merge reachable from the
tip and asks three questions. Did both sides arrive, or is
one parent an ancestor of the other, the redundant merge
that a fast-forward would have made invisible and honesty
would have skipped. Did the meeting produce anything, or
does the merged tree equal one parent's tree exactly, the
hollow merge where one side's work was taken whole and the
other's discarded, which is sometimes a decision and
always worth a look. And is the trunk standing where it
should, first parent by convention, because the foxtrot
merge that puts the trunk second quietly reverses what
first-parent history means, and every tool that walks
first parents afterward tells the story backwards. Clean
meetings are counted but not listed, in the fsck
tradition of not crying wolf over exhaust.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.repo import Repo


@dataclass(frozen=True)
class MergeFinding:
    address: str
    kind: str
    detail: str

    def line(self) -> str:
        return (
            f"  {self.address[:8]} [{self.kind}] "
            f"{self.detail}"
        )


def audit(
    repo: Repo, tip: str, trunk_tip: str | None = None
) -> tuple[int, list[MergeFinding]]:
    findings: list[MergeFinding] = []
    merges = 0
    trunk_line = (
        repo.graph.ancestors(trunk_tip)
        if trunk_tip is not None
        else set()
    )
    for address in repo.graph.ancestors(tip):
        commit = repo.graph.get(address)
        if len(commit.parents) < 2:
            continue
        merges += 1
        first, second = commit.parents[:2]
        if repo.graph.is_ancestor(second, first):
            findings.append(
                MergeFinding(
                    address=address,
                    kind="redundant",
                    detail=(
                        "the second parent was already "
                        "an ancestor of the first; a "
                        "fast-forward would have said "
                        "so honestly"
                    ),
                )
            )
            continue
        for parent, side in (
            (first, "first"),
            (second, "second"),
        ):
            if (
                repo.graph.get(parent).tree
                == commit.tree
            ):
                other = (
                    "second" if side == "first" else "first"
                )
                findings.append(
                    MergeFinding(
                        address=address,
                        kind="hollow",
                        detail=(
                            f"the tree equals the "
                            f"{side} parent's exactly; "
                            f"the {other} side's work "
                            "was discarded, sometimes "
                            "a decision, always worth "
                            "a look"
                        ),
                    )
                )
                break
        if (
            trunk_tip is not None
            and second in trunk_line
            and first not in trunk_line
        ):
            findings.append(
                MergeFinding(
                    address=address,
                    kind="foxtrot",
                    detail=(
                        "the trunk stands second; "
                        "every first-parent walk "
                        "afterward tells the story "
                        "backwards"
                    ),
                )
            )
    return merges, findings


def report(
    repo: Repo, tip: str, trunk_tip: str | None = None
) -> str:
    merges, findings = audit(repo, tip, trunk_tip)
    if not findings:
        return (
            f"{merges} meeting(s), all of them earned "
            "their commit; clean merges are counted, "
            "not listed"
        )
    lines = [
        f"{merges} meeting(s), {len(findings)} "
        "finding(s):"
    ]
    lines.extend(
        finding.line() for finding in findings
    )
    return "\n".join(lines)
