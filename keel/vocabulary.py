"""Vocabulary: the voice of a history, counted word by leading word.

Every repository develops a voice, and the census makes it
audible: leading words of subjects tallied, because the
first word is the verb of record and a history that opens
with fix half the time is describing its planning, not its
prose; subject lengths measured against the classic budget
of fifty, with the overruns counted rather than judged; and
the hedges tallied separately, the minors and the
just-a-quick, because hedging words in commit subjects are
apologies in advance and a rising apology rate is a team
smell wearing grammar. The fingerprint at the end is three
numbers, top verb share, average length, hedge rate, enough
to tell two repositories apart blind, and the census never
prescribes, in the doctor's tradition: the voice belongs to
the people who write in it, and the census only holds up
the mirror.
"""

from __future__ import annotations

from keel.repo import Repo

SUBJECT_BUDGET = 50
HEDGES = (
    "minor",
    "small",
    "quick",
    "just",
    "misc",
    "stuff",
)


def census(
    repo: Repo, tip: str
) -> dict[str, object]:
    subjects = [
        commit.message.splitlines()[0]
        for commit in repo.graph.log(tip)
    ]
    verbs: dict[str, int] = {}
    hedged = 0
    over_budget = 0
    total_length = 0
    for subject in subjects:
        words = subject.lower().split()
        if not words:
            continue
        first = words[0].rstrip(":!.")
        verbs[first] = verbs.get(first, 0) + 1
        if any(hedge in words for hedge in HEDGES):
            hedged += 1
        if len(subject) > SUBJECT_BUDGET:
            over_budget += 1
        total_length += len(subject)
    ranked = sorted(
        verbs.items(),
        key=lambda held: (-held[1], held[0]),
    )
    return {
        "subjects": len(subjects),
        "verbs": ranked,
        "hedged": hedged,
        "over_budget": over_budget,
        "average_length": (
            total_length / len(subjects)
            if subjects
            else 0.0
        ),
    }


def report(repo: Repo, tip: str) -> str:
    counted = census(repo, tip)
    subjects = counted["subjects"]
    ranked = counted["verbs"]
    lines = [
        f"the voice of {subjects} subject(s):"
    ]
    for verb, count in ranked[:3]:
        share = count * 100 // subjects
        lines.append(
            f"  opens with {verb!r} {count} time(s) "
            f"({share}%)"
        )
    top_verb, top_count = ranked[0]
    if top_verb == "fix" and (
        top_count * 2 >= subjects
    ):
        lines.append(
            "  half the history opens with fix; the "
            "voice is describing the planning, not "
            "the prose"
        )
    lines.append(
        f"  average subject {counted['average_length']:.0f} "
        f"character(s), {counted['over_budget']} over "
        f"the budget of {SUBJECT_BUDGET}"
    )
    hedge_rate = (
        counted["hedged"] * 100 // subjects
        if subjects
        else 0
    )
    lines.append(
        f"  hedges in {counted['hedged']} subject(s) "
        f"({hedge_rate}%); apologies in advance, "
        "counted, not judged"
    )
    lines.append(
        "the mirror only; the voice belongs to the "
        "people who write in it"
    )
    return "\n".join(lines)
