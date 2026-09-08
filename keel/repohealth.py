"""The health report: every examiner files one page, and nothing hides.

Each organ examines what it knows, the physical checks
bytes, the doctor checks the story, the census weighs the
attic, the branch count sorts the living from the lingering,
and the shape report names the graph, and this page is where
their findings sit side by side, because a repository is
never sick in one place at a time and a responder flipping
between five tools misses the correlation that is the actual
diagnosis. The sections keep their examiners' own words
rather than a summary voice, since paraphrase is where
precision goes to die. The one number this page adds is the
finding count, findings being things an examiner would say
out loud to a colleague, and the closing line scales with
it honestly: a clean report says so without fanfare, a
loud one counts its noise, and neither grades the
repository, because health is a conversation and a grade
is a conversation ender.
"""

from __future__ import annotations

from keel.fsck import Physical
from keel.graphstats import narrate as shape_narrate
from keel.historydoctor import examine
from keel.repo import Repo
from keel.sizes import report as sizes_report
from keel.stalebranches import census as branch_census


def health_report(
    repo: Repo, trunk: str = "main"
) -> str:
    tip = repo.refs.branches[trunk]
    findings = 0
    sections: list[str] = []

    physical = Physical(repo=repo).run()
    sections.append("the physical:\n  " + physical)
    if not physical.startswith("physical clean"):
        findings += 1

    symptoms = examine(repo, tip)
    if symptoms:
        findings += len(symptoms)
        story_lines = "\n".join(
            symptom.line() for symptom in symptoms
        )
        sections.append(
            f"the story ({len(symptoms)} finding(s)):\n"
            + story_lines
        )
    else:
        sections.append(
            "the story:\n  nothing the doctor would "
            "say out loud"
        )

    verdicts = branch_census(repo, trunk=trunk)
    lingering = [
        verdict
        for verdict in verdicts
        if verdict.verdict != "active"
    ]
    findings += len(lingering)
    if verdicts:
        branch_lines = "\n".join(
            verdict.line() for verdict in verdicts
        )
        sections.append("the branches:\n" + branch_lines)
    else:
        sections.append(
            "the branches:\n  only the trunk; nothing "
            "to judge"
        )

    attic = sizes_report(repo)
    sections.append("the attic:\n  " + attic.replace(
        "\n", "\n  "
    ))
    if "prescriptions:" in attic:
        findings += 1

    sections.append(
        "the shape:\n  "
        + shape_narrate(repo, tip).replace("\n", "\n  ")
    )

    if findings == 0:
        closing = (
            "no findings; a clean report, said without "
            "fanfare"
        )
    else:
        closing = (
            f"{findings} finding(s) across the "
            "examiners; correlations are the reader's "
            "to draw, and drawing them is the point of "
            "one page"
        )
    return "\n\n".join(
        [
            f"health report for {trunk} at {tip[:8]}:",
            *sections,
            closing,
        ]
    )
