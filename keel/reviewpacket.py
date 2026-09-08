"""The review packet: everything the reviewer opens, one envelope, no tabs.

Review quality is mostly determined before the first line
is read, by whether the reviewer knows what they are
looking at, and the packet answers the orientation
questions in one page: what each side did since the fork,
where the change landed by directory, who the owners file
says should be looking, and how the messages grade, which
sets expectations for how the code will read. The commit
list comes from the divergence question, never possession,
because reviewing commits the trunk already has is the
oldest wasted afternoon in the trade. The lint totals ride
along as advisory context in the lint's own graded-not-
blocked spirit, and when no owners file is configured the
packet says so instead of routing to nobody silently, since
an envelope with a missing section teaches reviewers to
stop trusting the envelope.
"""

from __future__ import annotations

from keel.branchdiff import since_we_parted
from keel.codeowners import OwnersFile
from keel.commitlint import lint_message
from keel.dirstat import render as dirstat_render
from keel.repo import Repo


def _touched_between(
    repo: Repo, fork: str, tip: str
) -> list[str]:
    old_files = repo.files_at(fork)
    new_files = repo.files_at(tip)
    return sorted(
        path
        for path in set(old_files) | set(new_files)
        if old_files.get(path) != new_files.get(path)
    )


def packet(
    repo: Repo,
    trunk: str,
    branch: str,
    owners: OwnersFile | None = None,
) -> str:
    our_side, their_side, fork = since_we_parted(
        repo, trunk, branch
    )
    branch_tip = repo.refs.branches[branch]
    sections: list[str] = [
        f"review packet: {branch} against {trunk}, "
        f"parted at {fork[:8]}"
    ]

    commit_lines = [
        f"under review ({len(their_side)} commit(s)):"
    ]
    lint_findings = 0
    for commit in their_side:
        lint_findings += len(
            lint_message(commit.message)
        )
        commit_lines.append(
            f"  {commit.address[:8]} "
            f"{commit.message.splitlines()[0]}"
        )
    if not their_side:
        commit_lines.append(
            "  nothing; this branch brought no commits"
        )
    sections.append("\n".join(commit_lines))

    if our_side:
        sections.append(
            f"meanwhile, {trunk} moved "
            f"{len(our_side)} commit(s); rebase or "
            "expect the merge to say so"
        )
    else:
        sections.append(
            f"{trunk} has not moved; this will land "
            "as written"
        )

    sections.append(
        dirstat_render(repo, fork, branch_tip)
    )

    touched = _touched_between(repo, fork, branch_tip)
    if owners is None:
        sections.append(
            "owners: no file configured; routing "
            "skipped and said so, because a missing "
            "section teaches reviewers to stop "
            "trusting the envelope"
        )
    else:
        routed = owners.route(touched)
        if routed["reviewers"]:
            sections.append(
                "owners: route to "
                + ", ".join(routed["reviewers"])
            )
        if routed["unclaimed"]:
            sections.append(
                "owners: unclaimed path(s): "
                + ", ".join(routed["unclaimed"])
            )

    sections.append(
        f"messages: {lint_findings} lint finding(s) "
        "across the branch; graded, not blocked, and "
        "a hint of how the code will read"
    )
    return "\n\n".join(sections)
