"""The inquest: from symptom to sentence in one narrated proceeding.

Finding the bad commit is half the job; the other half is
the twenty minutes of orientation that follow, and the
inquest folds both into one page. The hunt runs on the
automated oracle and arrives with its transcript, then the
proceeding examines the culprit the way the responder
actually needs: what the change said, which paths it
touched, and, the question nobody asks until it bites,
whether the culprit's lines are even still there. Blame at
the bad tip settles it, and when the lines have been
rewritten since, the page says the bug may have moved house,
because reverting a commit whose every line was already
replaced is theater performed on an empty stage. The page
ends with the two honest options, revert or fix forward,
and leaves the choosing to the person, since the inquest's
job is to make the choice informed, not to make it.
"""

from __future__ import annotations

from keel.bisectrun import AutoBisect, Oracle
from keel.blame import blame
from keel.repo import Repo


def _touched(repo: Repo, address: str) -> list[str]:
    commit = repo.graph.get(address)
    current = repo.files_at(address)
    if commit.parents:
        parent = repo.files_at(commit.parents[0])
    else:
        parent = {}
    return sorted(
        path
        for path in set(current) | set(parent)
        if current.get(path) != parent.get(path)
    )


def inquest(
    repo: Repo,
    good: str,
    bad: str,
    oracle: Oracle,
) -> str:
    hunt = AutoBisect(graph=repo.graph, oracle=oracle)
    culprit = hunt.run(good, bad)
    commit = repo.graph.get(culprit)
    subject = commit.message.splitlines()[0]
    touched = _touched(repo, culprit)
    lines = [
        f"verdict: {culprit[:8]} ({subject!r}) after "
        f"{len(hunt.answers)} oracle call(s)",
        f"the change: {len(touched)} path(s): "
        + ", ".join(touched),
    ]
    bad_files = repo.files_at(bad)
    still_there = 0
    for path in touched:
        if path not in bad_files:
            lines.append(
                f"  {path}: gone from the tip entirely"
            )
            continue
        owned = sum(
            1
            for row in blame(repo, bad, path)
            if row.commit == culprit
        )
        still_there += owned
        lines.append(
            f"  {path}: {owned} line(s) at the tip "
            "still written by the culprit"
        )
    if still_there == 0:
        lines.append(
            "every culprit line was since rewritten; "
            "the bug may have moved house, and "
            "reverting an empty stage is theater"
        )
    lines.append(
        "options: revert the culprit or fix forward; "
        "the transcript stands ready for appeal"
    )
    return "\n".join(lines)
