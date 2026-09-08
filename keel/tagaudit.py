"""The tag audit: version names checked for shape, order, and honesty.

Tags are permanent by design, which is exactly why their
mistakes are worth an audit before the next one lands. The
shape check reads each name against the versioned form, v
and numbers and dots, and files the rest under free-form,
not wrong but not sortable, because a release line where
v1.2 sorts next to project-alpha answers version questions
with a shrug. The order check is the honest one: versions
that compare higher must seal commits that come later, and
a v2.0 standing on an older commit than v1.9 is called an
anachronism by name, since whoever reads the tags as a
timeline, and everyone does, is being quietly lied to. The
audit also names the gaps in the major line, missing
majors being either history or a numbering accident, and
the audit cannot tell which, so it asks rather than
concludes, in the census tradition.
"""

from __future__ import annotations

import re

from keel.repo import Repo
from keel.tags import TagStore

VERSIONED = re.compile(
    r"^v(\d+)\.(\d+)(?:\.(\d+))?$"
)


def _key(name: str) -> tuple[int, int, int] | None:
    found = VERSIONED.match(name)
    if not found:
        return None
    major, minor, patch = found.groups()
    return (
        int(major),
        int(minor),
        int(patch or 0),
    )


def audit(repo: Repo, tags: TagStore) -> str:
    versioned: list[tuple[tuple[int, int, int], str]] = []
    freeform: list[str] = []
    for name in tags.tags:
        key = _key(name)
        if key is None:
            freeform.append(name)
        else:
            versioned.append((key, name))
    versioned.sort()
    lines = [
        f"{len(versioned)} versioned tag(s), "
        f"{len(freeform)} free-form"
    ]
    for name in sorted(freeform):
        lines.append(
            f"  free-form: {name}; not wrong, not "
            "sortable"
        )
    anachronisms = 0
    for index in range(1, len(versioned)):
        _low_key, low_name = versioned[index - 1]
        _high_key, high_name = versioned[index]
        low_seq = repo.graph.get(
            tags.resolve(low_name)
        ).sequence
        high_seq = repo.graph.get(
            tags.resolve(high_name)
        ).sequence
        if high_seq < low_seq:
            anachronisms += 1
            lines.append(
                f"  anachronism: {high_name} seals an "
                f"older commit (seq {high_seq}) than "
                f"{low_name} (seq {low_seq}); whoever "
                "reads the tags as a timeline is "
                "being quietly lied to"
            )
    majors = sorted(
        {key[0] for key, _name in versioned}
    )
    if majors:
        missing = [
            str(expected)
            for expected in range(
                majors[0], majors[-1] + 1
            )
            if expected not in majors
        ]
        if missing:
            lines.append(
                "  missing major(s): "
                + ", ".join(missing)
                + "; history or a numbering accident, "
                "and the audit asks rather than "
                "concludes"
            )
    if (
        not freeform
        and not anachronisms
        and (not majors or len(lines) == 1)
    ):
        lines.append(
            "the line reads clean; versions sort, "
            "seals agree with time"
        )
    return "\n".join(lines)
