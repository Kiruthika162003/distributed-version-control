"""The transplant: a whole topic moved between branches, judged as one.

Cherry-picking a topic one commit at a time invites the
partial transplant, three of five commits moved and the
topic broken on both branches, so the transplant gathers
first and judges whole: every commit on the source line
whose subject carries the topic marker, in their original
order, each checked against the destination the way the
backport checks its patients, and the operation proceeds
only when every member applies cleanly, because a topic is
one idea wearing several commits and half an idea helps
nobody. The landed copies name their origins in the
backport's own style, and the report of a refused
transplant lists which member blocked it and why, the
diverged file named, so the fix is surgical rather than a
retreat to moving everything by hand, which is where
partial transplants come from in the first place.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Conflict, Invalid
from keel.repo import Repo


def gather(
    repo: Repo, source: str, marker: str
) -> list[Commit]:
    if not marker.strip():
        raise Invalid(
            "an empty marker gathers everything, "
            "and everything is not a topic"
        )
    tip = repo.refs.branches.get(source)
    if tip is None:
        raise Invalid(
            f"{source} is not a branch here"
        )
    chain = []
    cursor = tip
    while True:
        commit = repo.graph.get(cursor)
        chain.append(commit)
        if not commit.parents:
            break
        cursor = commit.parents[0]
    chain.reverse()
    return [
        commit
        for commit in chain
        if marker in commit.message.splitlines()[0]
        and len(commit.parents) == 1
    ]


def transplant(
    repo: Repo,
    source: str,
    destination: str,
    marker: str,
) -> str:
    members = gather(repo, source, marker)
    if not members:
        raise Invalid(
            f"no commits on {source} carry "
            f"{marker!r}; a transplant needs a topic "
            "to move"
        )
    if destination not in repo.refs.branches:
        raise Invalid(
            f"{destination} is not a branch here"
        )
    landing_files = dict(
        repo.files_at(repo.refs.branches[destination])
    )
    staged = []
    for commit in members:
        parent_files = repo.files_at(
            commit.parents[0]
        )
        current = repo.files_at(commit.address)
        changes = {}
        for path in set(current) | set(parent_files):
            if current.get(path) != parent_files.get(
                path
            ):
                changes[path] = current.get(path)
        for path, content in changes.items():
            held = landing_files.get(path)
            expected = parent_files.get(path)
            if held not in (expected, content):
                raise Conflict(
                    f"the transplant is refused "
                    f"whole: {commit.address[:8]} "
                    f"({commit.message.splitlines()[0]!r}) "
                    f"finds {path} diverged on "
                    f"{destination}; a topic is one "
                    "idea wearing several commits, "
                    "and half an idea helps nobody"
                )
        for path, content in changes.items():
            if content is None:
                landing_files.pop(path, None)
            else:
                landing_files[path] = content
        staged.append((commit, dict(landing_files)))
    previous = repo.refs.branches[destination]
    for commit, snapshot in staged:
        created = repo.commit_with_parents(
            snapshot,
            commit.message
            + f"\n\n(transplanted from "
            f"{commit.address[:8]})",
            (previous,),
        )
        previous = created.address
    repo.refs.move(
        destination,
        previous,
        reason=f"transplant {marker!r}",
    )
    return (
        f"transplanted {len(staged)} commit(s) "
        f"carrying {marker!r} from {source} to "
        f"{destination}, judged as one and landed "
        "as one"
    )
