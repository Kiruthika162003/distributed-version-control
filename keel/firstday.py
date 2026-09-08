"""The first day: a tour of the repository for whoever just arrived.

Onboarding documents rot because they are written once and
the repository keeps moving, so the tour is computed instead
of written: where the tip stands and what era the tags say
it belongs to, what shape the history makes, which files
carry the most action, and whom the owners file suggests
asking, each read live from the organs that know. The
closing section is the part no wiki has: the last five
commit subjects verbatim, because they are the current
conversation, and joining a team is mostly learning what
the conversation already is. Every optional organ that is
absent is named as absent with a working fallback, ask
whoever answers, since the newcomer's worst first day is
the one spent discovering which parts of the map were
drawn hopefully.
"""

from __future__ import annotations

from keel.codeowners import OwnersFile
from keel.describe import describe_head
from keel.graphstats import measure
from keel.hotspots import census as hotspot_census
from keel.repo import Repo
from keel.tags import TagStore


def tour(
    repo: Repo,
    trunk: str = "main",
    tags: TagStore | None = None,
    owners: OwnersFile | None = None,
) -> str:
    tip = repo.refs.branches[trunk]
    commits = repo.graph.log(tip)
    sections: list[str] = [
        f"welcome; {trunk} stands at {tip[:8]} with "
        f"{len(commits)} commit(s) behind it"
    ]

    if tags is not None:
        sections.append(
            "the era: " + describe_head(repo, tags)
        )
    else:
        sections.append(
            "the era: no tags placed yet; history "
            "without milestones reads longer than "
            "it is"
        )

    shape = measure(repo, tip)
    sections.append(
        f"the shape: {shape.merges} merge(s) in "
        f"{shape.commits} commit(s), longest quiet "
        f"run {shape.longest_linear_run}; "
        + shape.verdicts()[0]
    )

    spots, _ghosts = hotspot_census(repo, tip)
    if spots:
        busiest = spots[:2]
        spot_lines = "; ".join(
            f"{spot.path} ({spot.touches} touch(es), "
            f"{spot.size} byte(s))"
            for spot in busiest
        )
        sections.append(
            "the busy ground: " + spot_lines
            + "; start reading there, everyone else "
            "does"
        )

    if owners is not None and owners.rules:
        sample = owners.rules[0]
        sections.append(
            f"who to ask: {len(owners.rules)} routing "
            f"rule(s); for instance {sample.pattern} "
            "answers to "
            + ", ".join(sample.owners)
        )
    else:
        sections.append(
            "who to ask: no owners file; ask whoever "
            "answers, and consider writing the file "
            "your first contribution"
        )

    recent = [
        commit.message.splitlines()[0]
        for commit in commits[:5]
    ]
    conversation = "\n".join(
        f"  {subject}" for subject in recent
    )
    sections.append(
        "the current conversation, last "
        f"{len(recent)} subject(s):\n" + conversation
    )
    return "\n\n".join(sections)
