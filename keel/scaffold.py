"""The scaffold: a repository's first commit, standing straight from birth.

New repositories inherit their habits from their first
afternoon, and the scaffold spends that afternoon well: one
founding commit carrying the small set of files every later
audit will ask about, a README that states the project's
name and one honest sentence, an ignore file seeded with
the universal exhaust patterns, and, when a license header
is declared, a LICENSE file holding it, so the license
auditor's first run finds its anchor instead of an absence.
The scaffold refuses a repository that already has commits,
retrofitting being a different job with different risks,
and refuses an empty project name, a repository with no
name being unfindable in every list it will ever appear
in. The receipt names each file laid down, because the
first commit is the one everyone eventually reads, and it
may as well read as a plan.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Invalid
from keel.repo import Repo

EXHAUST_PATTERNS = (
    "__pycache__/",
    "*.pyc",
    "*.log",
    "build/",
)


def found(
    repo: Repo,
    name: str,
    sentence: str,
    license_header: str = "",
) -> tuple[Commit, str]:
    if repo.refs.branches:
        raise Invalid(
            "this repository already has commits; "
            "retrofitting is a different job with "
            "different risks"
        )
    if not name.strip():
        raise Invalid(
            "a repository with no name is unfindable "
            "in every list it will ever appear in"
        )
    if not sentence.strip():
        raise Invalid(
            "the one honest sentence is required; a "
            "README that says nothing teaches "
            "nothing"
        )
    files = {
        "README.md": (
            f"# {name.strip()}\n\n"
            f"{sentence.strip()}\n"
        ).encode(),
        ".ignore": (
            "\n".join(EXHAUST_PATTERNS) + "\n"
        ).encode(),
    }
    if license_header.strip():
        files["LICENSE"] = (
            license_header.strip() + "\n"
        ).encode()
    commit = repo.commit(
        files, f"found {name.strip()}"
    )
    laid = ", ".join(sorted(files))
    return commit, (
        f"{name.strip()} founded at "
        f"{commit.address[:8]}; laid down {laid}. "
        "The first commit is the one everyone "
        "eventually reads, and this one reads as a "
        "plan"
    )
