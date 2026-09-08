"""Pilotage: the first landing walked through before it is attempted.

A first push fails on rules the newcomer has never seen,
and pilotage runs the rules in rehearsal: the branch name
against the naming policy, the message against the lint,
the touched paths against the owners file for who will
review, and each verdict is delivered as coaching rather
than refusal, this WOULD bounce and here is the sentence
to fix it, because the difference between a gate and a
mentor is timing, the same rule enforced after the attempt
is a gate and explained before it is a mentor. The
rehearsal never touches the harbor's real machinery, no
journals written, no refusals logged, since a practice
landing that leaves records teaches newcomers to practice
somewhere unwatched, and the closing line says plainly
whether the real landing would clear today, with the
count of sentences to fix first when it would not.
"""

from __future__ import annotations

from keel.branchpolicy import NamingPolicy
from keel.codeowners import OwnersFile
from keel.commitlint import lint_message
from keel.errors import Invalid


def rehearse(
    branch: str,
    message: str,
    touched_paths: list[str],
    policy: NamingPolicy | None = None,
    owners: OwnersFile | None = None,
) -> str:
    fixes = 0
    lines = [f"pilotage for {branch}:"]

    if policy is None:
        lines.append(
            "  naming: no policy aboard; any name "
            "sails today"
        )
    else:
        try:
            verdict = policy.check(branch)
            lines.append(f"  naming: {verdict}")
        except Invalid as coaching:
            fixes += 1
            lines.append(
                f"  naming: this WOULD bounce; "
                f"{coaching}"
            )

    findings = lint_message(message)
    if findings:
        fixes += len(findings)
        lines.append(
            f"  message: {len(findings)} finding(s) "
            "the lint would grade:"
        )
        lines.extend(
            f"    {finding.line()}"
            for finding in findings
        )
    else:
        lines.append(
            "  message: clean; the 2am reader thanks "
            "you in advance"
        )

    if owners is None:
        lines.append(
            "  review: no owners file; ask whoever "
            "answers"
        )
    else:
        routed = owners.route(list(touched_paths))
        if routed["reviewers"]:
            lines.append(
                "  review: expect "
                + ", ".join(routed["reviewers"])
            )
        if routed["unclaimed"]:
            fixes += 1
            lines.append(
                "  review: "
                + ", ".join(routed["unclaimed"])
                + " unclaimed; this WOULD need an "
                "owner before landing"
            )

    if fixes == 0:
        lines.append(
            "the real landing would clear today; "
            "same rules, no surprises"
        )
    else:
        lines.append(
            f"{fixes} sentence(s) to fix before the "
            "real attempt; a rule explained before "
            "the attempt is a mentor, after it a gate"
        )
    return "\n".join(lines)
