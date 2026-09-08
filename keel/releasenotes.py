"""Release notes: the changelog, the address, and the seal in one document.

A release announcement is three claims stapled together,
what changed, which bytes are meant, and how to check, and
the composer staples them from the organs that own each:
the changelog drafted between the last tag and the tip with
breaking changes never buried, the tip's address stated
plainly because the address is the release and version
strings are its nickname, and the checksum for whoever
receives the artifact somewhere addresses cannot follow.
Composing a release of nothing is refused, a version bump
with no commits being marketing's problem and not history's,
and the cut operation is compose plus the tag placed in one
motion, so the document and the seal can never describe
different commits, which is the precise failure mode of
writing announcements by hand on release day.
"""

from __future__ import annotations

from keel.archive import release_checksum
from keel.changelog import render_changelog
from keel.errors import Invalid
from keel.repo import Repo
from keel.tags import TagStore


def compose(
    repo: Repo,
    tags: TagStore,
    since: str,
    version: str,
) -> str:
    previous = tags.resolve(since)
    tip = repo.refs.current()
    if previous == tip:
        raise Invalid(
            f"nothing landed since {since}; a version "
            "bump with no commits is marketing's "
            "problem, not history's"
        )
    changelog = render_changelog(
        repo, previous, tip, version
    )
    checksum = release_checksum(repo, tip)
    return "\n".join(
        [
            f"{version}, cut at {tip[:8]}; the "
            "address is the release, the version "
            "is its nickname",
            "",
            changelog,
            "",
            f"checksum: {checksum}",
            "verify the artifact against the "
            "checksum where addresses cannot follow",
        ]
    )


def cut(
    repo: Repo,
    tags: TagStore,
    since: str,
    version: str,
    message: str,
) -> tuple[str, str]:
    notes = compose(repo, tags, since, version)
    receipt = tags.place(
        version, repo.refs.current(), message
    )
    return notes, (
        receipt
        + "; the document and the seal name the same "
        "commit by construction"
    )
