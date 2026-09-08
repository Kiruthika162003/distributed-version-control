"""Branch difference: two dots, three dots, and the confusion priced in.

The two-dot question and the three-dot question sound alike
and answer differently, which is why every team has a story
about reviewing the wrong commits. Two dots is possession:
what does theirs have that ours lacks, the question asked
before a pull. Three dots is divergence: what has each side
done since the fork point, the question a reviewer means
almost every time, and the fork point is found honestly via
the merge base rather than assumed. This module makes the
caller choose the question by name, only_theirs or
since_we_parted, because dots are a notation for people who
already know the difference and a trap for everyone else,
and the rendered page repeats the question it answered in
plain words at the top, so the wrong-commits story, when it
happens anyway, at least cannot blame the tool.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Missing
from keel.repo import Repo


def _tip(repo: Repo, branch: str) -> str:
    tip = repo.refs.branches.get(branch)
    if tip is None:
        raise Missing(f"{branch} is not a branch here")
    return tip


def _ordered(
    repo: Repo, addresses: set[str]
) -> list[Commit]:
    found = [
        repo.graph.get(address) for address in addresses
    ]
    found.sort(key=lambda commit: -commit.sequence)
    return found


def only_theirs(
    repo: Repo, ours: str, theirs: str
) -> list[Commit]:
    our_line = repo.graph.ancestors(_tip(repo, ours))
    their_line = repo.graph.ancestors(
        _tip(repo, theirs)
    )
    return _ordered(repo, their_line - our_line)


def since_we_parted(
    repo: Repo, ours: str, theirs: str
) -> tuple[list[Commit], list[Commit], str]:
    our_tip = _tip(repo, ours)
    their_tip = _tip(repo, theirs)
    fork = repo.graph.merge_base(our_tip, their_tip)
    fork_line = repo.graph.ancestors(fork)
    our_side = _ordered(
        repo,
        repo.graph.ancestors(our_tip) - fork_line,
    )
    their_side = _ordered(
        repo,
        repo.graph.ancestors(their_tip) - fork_line,
    )
    return our_side, their_side, fork


def render(
    repo: Repo,
    ours: str,
    theirs: str,
    question: str,
) -> str:
    if question == "only_theirs":
        commits = only_theirs(repo, ours, theirs)
        lines = [
            f"what {theirs} has that {ours} lacks "
            "(possession, the pre-pull question):"
        ]
        lines.extend(
            f"  {commit.address[:8]} "
            f"{commit.message.splitlines()[0]}"
            for commit in commits
        )
        if not commits:
            lines.append(
                f"  nothing; {ours} already holds "
                f"all of {theirs}"
            )
        return "\n".join(lines)
    if question == "since_we_parted":
        our_side, their_side, fork = since_we_parted(
            repo, ours, theirs
        )
        lines = [
            f"since {ours} and {theirs} parted at "
            f"{fork[:8]} (divergence, the review "
            "question):"
        ]
        lines.append(f"  {ours} did:")
        lines.extend(
            f"    {commit.address[:8]} "
            f"{commit.message.splitlines()[0]}"
            for commit in our_side
        )
        if not our_side:
            lines.append("    nothing")
        lines.append(f"  {theirs} did:")
        lines.extend(
            f"    {commit.address[:8]} "
            f"{commit.message.splitlines()[0]}"
            for commit in their_side
        )
        if not their_side:
            lines.append("    nothing")
        return "\n".join(lines)
    raise Missing(
        f"{question!r} is not a question here; ask "
        "only_theirs or since_we_parted, because dots "
        "are a trap for everyone who has not already "
        "been burned"
    )
