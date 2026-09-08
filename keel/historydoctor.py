"""The history doctor: a physical for the story, not the storage.

Fsck checks that the bytes are honest; nobody checks that
the narrative is, and narratives rot in known ways. The
doctor examines a line of history for five findings: fixup
commits that outlived their review and never got folded,
work-in-progress markers that became permanent residents,
merge commits wearing the default message that says nothing
a graph walk would not, boulders that touch more paths than
any reviewer can hold in mind at once, and stutters, runs
of consecutive commits with the same subject, which usually
mean one logical change was saved like a video game. Every
finding names its commit and its remedy, and the thresholds
sit in constants at the top of the file where policy
arguments belong. The doctor never blocks anything, in the
lint's own tradition: history already happened, and the
useful output is a to-do list for the next rewrite, not a
lecture about the last one.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.repo import Repo

BOULDER_PATHS = 8
STUTTER_RUN = 3
WIP_MARKERS = ("wip", "tmp", "checkpoint")
DEFAULT_MERGE_PREFIXES = ("merge branch", "merge the")


@dataclass(frozen=True)
class Symptom:
    address: str
    kind: str
    detail: str
    remedy: str

    def line(self) -> str:
        return (
            f"  {self.address[:8]} [{self.kind}] "
            f"{self.detail}; {self.remedy}"
        )


def _subject(message: str) -> str:
    return message.splitlines()[0]


def _first_parent_chain(repo: Repo, tip: str) -> list:
    chain = []
    cursor = tip
    while True:
        commit = repo.graph.get(cursor)
        chain.append(commit)
        if not commit.parents:
            break
        cursor = commit.parents[0]
    chain.reverse()
    return chain


def _touched_count(repo: Repo, commit) -> int:
    current = repo.files_at(commit.address)
    if not commit.parents:
        return len(current)
    parent = repo.files_at(commit.parents[0])
    return sum(
        1
        for path in set(current) | set(parent)
        if current.get(path) != parent.get(path)
    )


def examine(repo: Repo, tip: str) -> list[Symptom]:
    chain = _first_parent_chain(repo, tip)
    symptoms: list[Symptom] = []
    run_subject = ""
    run_length = 0
    for commit in chain:
        subject = _subject(commit.message)
        lowered = subject.lower()
        if lowered.startswith(("fixup! ", "squash! ")):
            symptoms.append(
                Symptom(
                    address=commit.address,
                    kind="unfolded",
                    detail=(
                        f"{subject!r} outlived its review"
                    ),
                    remedy=(
                        "autosquash before anyone "
                        "bisects through it"
                    ),
                )
            )
        if any(
            lowered == marker
            or lowered.startswith(marker + " ")
            or lowered.startswith(marker + ":")
            for marker in WIP_MARKERS
        ):
            symptoms.append(
                Symptom(
                    address=commit.address,
                    kind="squatter",
                    detail=(
                        f"{subject!r} was a checkpoint, "
                        "now a resident"
                    ),
                    remedy="reword it to say what it did",
                )
            )
        if len(commit.parents) > 1 and any(
            lowered.startswith(prefix)
            for prefix in DEFAULT_MERGE_PREFIXES
        ):
            symptoms.append(
                Symptom(
                    address=commit.address,
                    kind="mute-merge",
                    detail=(
                        "a merge message a graph walk "
                        "could have written"
                    ),
                    remedy=(
                        "say why the lines met, not "
                        "that they did"
                    ),
                )
            )
        touched = _touched_count(repo, commit)
        if touched > BOULDER_PATHS:
            symptoms.append(
                Symptom(
                    address=commit.address,
                    kind="boulder",
                    detail=(
                        f"{touched} path(s) in one "
                        f"commit, past the line of "
                        f"{BOULDER_PATHS}"
                    ),
                    remedy=(
                        "split by intention next time; "
                        "reviewers hold ideas, not files"
                    ),
                )
            )
        if subject == run_subject:
            run_length += 1
            if run_length == STUTTER_RUN:
                symptoms.append(
                    Symptom(
                        address=commit.address,
                        kind="stutter",
                        detail=(
                            f"{subject!r} repeated "
                            f"{STUTTER_RUN} time(s) "
                            "running"
                        ),
                        remedy=(
                            "one logical change saved "
                            "like a video game; squash "
                            "the run"
                        ),
                    )
                )
        else:
            run_subject = subject
            run_length = 1
    return symptoms


def checkup(repo: Repo, tip: str) -> str:
    symptoms = examine(repo, tip)
    if not symptoms:
        return (
            "the story checks out; the doctor has "
            "nothing to add"
        )
    lines = [
        f"{len(symptoms)} finding(s), none blocking; "
        "history already happened"
    ]
    lines.extend(symptom.line() for symptom in symptoms)
    lines.append(
        "a to-do list for the next rewrite, not a "
        "lecture about the last one"
    )
    return "\n".join(lines)
