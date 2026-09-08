"""Commit message lint: history is documentation, so the entries get edited.

Nobody rereads code comments as often as they reread history
under pressure, at two in the morning, mid-incident, and the
lint enforces the shape that reads well then: a subject
under the length limit that does not end in a period, a
blank line before the body because tooling everywhere
assumes it, body lines wrapped where terminals put them, and
a subject that says what changed rather than opening with
noise words the reader must skip. Every finding carries the
rule name and the fix, findings accumulate rather than
stopping at the first, because a message with three problems
deserves one round trip, and the lint grades rather than
blocks by default since the goal is better messages, not
fewer commits, and a gate this opinionated earns bypass
resentment faster than any other.
"""

from __future__ import annotations

from dataclasses import dataclass

SUBJECT_LIMIT = 62
BODY_WRAP = 72
NOISE_OPENERS = (
    "fixed stuff",
    "misc",
    "changes",
    "update",
    "updates",
    "wip",
)


@dataclass(frozen=True)
class LintFinding:
    rule: str
    complaint: str
    fix: str

    def line(self) -> str:
        return f"{self.rule}: {self.complaint}; {self.fix}"


def lint_message(message: str) -> list[LintFinding]:
    findings: list[LintFinding] = []
    lines = message.splitlines()
    subject = lines[0] if lines else ""
    if not subject.strip():
        findings.append(
            LintFinding(
                rule="subject-exists",
                complaint="the message opens with nothing",
                fix="say what changed in the first line",
            )
        )
        return findings
    if len(subject) > SUBJECT_LIMIT:
        findings.append(
            LintFinding(
                rule="subject-length",
                complaint=(
                    f"the subject runs {len(subject)} "
                    f"characters against {SUBJECT_LIMIT}"
                ),
                fix="move the detail into the body",
            )
        )
    if subject.rstrip().endswith("."):
        findings.append(
            LintFinding(
                rule="subject-period",
                complaint="the subject ends with a period",
                fix="subjects are titles, not sentences",
            )
        )
    lowered = subject.lower()
    for opener in NOISE_OPENERS:
        if lowered == opener or lowered.startswith(
            opener + " "
        ):
            findings.append(
                LintFinding(
                    rule="subject-noise",
                    complaint=(
                        f"the subject opens with "
                        f"{opener!r}, which the 2am reader "
                        "must skip"
                    ),
                    fix="name the change, not the mood",
                )
            )
            break
    if len(lines) > 1 and lines[1].strip():
        findings.append(
            LintFinding(
                rule="blank-before-body",
                complaint=(
                    "the body starts without a blank line"
                ),
                fix=(
                    "tooling everywhere assumes the blank; "
                    "give it one"
                ),
            )
        )
    for number, line in enumerate(lines[2:], start=3):
        if len(line) > BODY_WRAP:
            findings.append(
                LintFinding(
                    rule="body-wrap",
                    complaint=(
                        f"line {number} runs {len(line)} "
                        f"characters against {BODY_WRAP}"
                    ),
                    fix="wrap where terminals do",
                )
            )
            break
    return findings


def grade(message: str) -> str:
    findings = lint_message(message)
    if not findings:
        return "clean; the 2am reader thanks you"
    lines = [
        f"{len(findings)} finding(s), one round trip:"
    ]
    lines.extend(
        f"  {finding.line()}" for finding in findings
    )
    lines.append(
        "graded, not blocked; the goal is better messages, "
        "not fewer commits"
    )
    return "\n".join(lines)
