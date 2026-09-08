"""Remote pruning: observations of the departed, retired with a receipt.

The remote-tracking cache records where their branches
stood at the last fetch, and branches deleted upstream
leave observations behind, still quoted by status lines,
still offered by completions, ghosts with good posture.
The audit compares the observations against the remote as
it stands and sorts the difference honestly: observed and
still real, observed but gone upstream, and real but never
observed, the last being not a ghost but a stranger the
next fetch will introduce. Pruning retires only the
ghosts, one receipt per retirement naming where the
observation last stood, because a completion that stops
offering a branch should leave a note saying why, and the
audit never touches the remote itself, being a janitor of
local beliefs and not of other people's repositories.
"""

from __future__ import annotations

from keel.errors import Missing
from keel.remotes import RemoteSet


def audit(
    remotes: RemoteSet, name: str
) -> dict[str, list[str]]:
    remote = remotes.remotes.get(name)
    if remote is None:
        raise Missing(f"{name} is not a remote")
    observed = set(remote.observed)
    actual = set(remote.repo.refs.branches)
    return {
        "standing": sorted(observed & actual),
        "ghosts": sorted(observed - actual),
        "strangers": sorted(actual - observed),
    }


def report(remotes: RemoteSet, name: str) -> str:
    sorted_out = audit(remotes, name)
    lines = [
        f"observations of {name}: "
        f"{len(sorted_out['standing'])} standing, "
        f"{len(sorted_out['ghosts'])} ghost(s), "
        f"{len(sorted_out['strangers'])} stranger(s)"
    ]
    for branch in sorted_out["ghosts"]:
        lines.append(
            f"  ghost: {branch}; gone upstream, "
            "still quoted here with good posture"
        )
    for branch in sorted_out["strangers"]:
        lines.append(
            f"  stranger: {branch}; the next fetch "
            "will make the introduction"
        )
    if not sorted_out["ghosts"] and not (
        sorted_out["strangers"]
    ):
        lines.append(
            "beliefs and reality agree; the janitor "
            "leans on the broom"
        )
    return "\n".join(lines)


def prune(remotes: RemoteSet, name: str) -> str:
    remote = remotes.remotes.get(name)
    if remote is None:
        raise Missing(f"{name} is not a remote")
    ghosts = audit(remotes, name)["ghosts"]
    if not ghosts:
        return (
            f"nothing to prune on {name}; no ghosts "
            "among the observations"
        )
    receipts = []
    for branch in ghosts:
        stood = remote.observed.pop(branch)
        receipts.append(
            f"  retired the observation of {branch}, "
            f"last seen at {stood[:8]}; the "
            "completion stops offering it, and this "
            "is the note saying why"
        )
    return "\n".join(
        [
            f"pruned {len(ghosts)} ghost(s) from "
            f"{name}:",
            *receipts,
        ]
    )
