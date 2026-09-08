"""Whereis: exact bytes hunted across every commit and every name.

The forensic question arrives after the leak or before the
dedupe, where else do these exact bytes live, and the hunt
answers it across the whole history: every commit whose
tree carries the content, under whatever path it wore
there, grouped into residencies, a path plus the commit
range it held the bytes, because the useful answer is not
four hundred commit addresses but config.env held this
from sequence 3 to sequence 90. The search is by content
address, exact by construction, and the miss is
definitive in a way text search never is: these bytes
have never been committed here, said flatly, which for a
leaked secret is the sentence everyone was hoping to
hear and should still verify against the reflog's
unpushed corners. Residencies still standing at a branch
tip are marked live, since bytes still reachable are
bytes still leaking.
"""

from __future__ import annotations

from keel.objects import BLOB, digest_bytes
from keel.repo import Repo


def residencies(
    repo: Repo, content: bytes
) -> list[tuple[str, int, int, bool]]:
    wanted = digest_bytes(BLOB, content)
    sightings: dict[str, list[int]] = {}
    for commit in sorted(
        repo.graph.commits.values(),
        key=lambda held: held.sequence,
    ):
        for path, blob in repo.trees.read_tree(
            commit.tree
        ).items():
            if blob == wanted:
                sightings.setdefault(path, []).append(
                    commit.sequence
                )
    live_paths = set()
    for tip in repo.refs.branches.values():
        for path, blob in repo.trees.read_tree(
            repo.graph.get(tip).tree
        ).items():
            if blob == wanted:
                live_paths.add(path)
    return [
        (
            path,
            min(sequences),
            max(sequences),
            path in live_paths,
        )
        for path, sequences in sorted(
            sightings.items()
        )
    ]


def report(repo: Repo, content: bytes) -> str:
    found = residencies(repo, content)
    if not found:
        return (
            "these bytes have never been committed "
            "here; said flatly, and still worth "
            "verifying against the reflog's "
            "unpushed corners"
        )
    lines = [
        f"{len(found)} residenc(ies) for these "
        f"{len(content)} byte(s):"
    ]
    for path, first, last, live in found:
        span = (
            f"seq {first}"
            if first == last
            else f"seq {first} to {last}"
        )
        marker = (
            "; LIVE at a branch tip, still "
            "reachable and still leaking"
            if live
            else "; historical only"
        )
        lines.append(f"  {path}: {span}{marker}")
    return "\n".join(lines)
