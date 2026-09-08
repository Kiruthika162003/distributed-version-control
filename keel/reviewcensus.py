"""The review census: who vouches, how often, and which keys are typos.

Trailers are the machine-readable margin of the commit
message, and the census reads two things out of them. The
reviewers first: every Reviewed-by name counted across the
line, ranked, with the concentration stated when the top
two carry more than two thirds, because review load that
lives with two people is a bus factor wearing a compliment,
and the number should be said while both are still here.
The keys second: every trailer key in use inventoried, and
the near-misses of the known keys called out by edit
distance, Reviewd-by and Signed-of-by being typos that
silently exempt their commits from every count that
matters, which is worse than no trailer because it looks
like one. The census reads and never blocks, the
commitlint's territory being enforcement and this page
being the map of what actually got written.
"""

from __future__ import annotations

from keel.repo import Repo
from keel.trailers import query

KNOWN_KEYS = (
    "reviewed-by",
    "signed-off-by",
    "co-authored-by",
    "fixes",
)
CONCENTRATION = 2 / 3


def _edit_close(left: str, right: str) -> bool:
    if left == right:
        return False
    if abs(len(left) - len(right)) > 1:
        return False
    shorter, longer = sorted(
        (left, right), key=len
    )
    for index in range(len(longer)):
        if shorter == longer[:index] + longer[
            index + 1:
        ]:
            return True
    if len(left) == len(right):
        differences = sum(
            1
            for a, b in zip(left, right, strict=True)
            if a != b
        )
        return differences == 1
    return False


def _keys_in(message: str) -> list[str]:
    found = []
    for line in message.splitlines():
        if ":" not in line:
            continue
        key = line.split(":", 1)[0].strip().lower()
        if key and " " not in key and "-" in key:
            found.append(key)
    return found


def census(repo: Repo, tip: str) -> str:
    reviewers: dict[str, int] = {}
    keys: dict[str, int] = {}
    total_reviews = 0
    for commit in repo.graph.log(tip):
        for name in query(
            commit.message, "reviewed-by"
        ):
            reviewers[name] = (
                reviewers.get(name, 0) + 1
            )
            total_reviews += 1
        for key in _keys_in(commit.message):
            keys[key] = keys.get(key, 0) + 1
    lines = [
        f"{total_reviews} review vouch(es) from "
        f"{len(reviewers)} reviewer(s):"
    ]
    ranked = sorted(
        reviewers.items(),
        key=lambda held: (-held[1], held[0]),
    )
    for name, count in ranked:
        lines.append(f"  {name}: {count}")
    if len(ranked) >= 2 and total_reviews:
        top_two = ranked[0][1] + ranked[1][1]
        if top_two / total_reviews > CONCENTRATION:
            lines.append(
                "  the top two carry "
                f"{top_two} of {total_reviews}; a "
                "bus factor wearing a compliment, "
                "said while both are still here"
            )
    typos = []
    for key in sorted(keys):
        for known in KNOWN_KEYS:
            if _edit_close(key, known):
                typos.append(
                    f"  near-miss: {key!r} "
                    f"({keys[key]} use(s)) is one "
                    f"slip from {known!r}; it looks "
                    "like a trailer and counts as "
                    "nothing"
                )
    lines.extend(typos)
    if not typos:
        lines.append(
            "  every trailer key spells itself; the "
            "counts can be trusted"
        )
    return "\n".join(lines)
