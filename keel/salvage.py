"""Salvage: content raised from any depth, with the provenance attached.

Every version of every file still exists somewhere below
the waterline, and salvage is the dive that brings one
back: name the commit and the path and receive the bytes,
with a provenance line stating exactly where they came
from, because recovered content without its origin becomes
folklore in a week, the file someone found somewhere that
now lives in three chats. A path missing at the named
depth is answered with the paths that were there, nearest
names first, since the diver who asked for utils.py when
the era called it helpers.py deserves the correction
rather than an empty net. The raise-and-commit form lands
the salvaged bytes as a real commit whose message carries
the provenance, so the recovery is itself history, and
the one refusal is raising bytes identical to what the
tip already holds, a dive after something already on
deck.
"""

from __future__ import annotations

from keel.errors import Invalid, Missing
from keel.repo import Repo


def _closest(
    wanted: str, available: list[str]
) -> list[str]:
    stem = wanted.rsplit("/", 1)[-1].lower()
    scored = []
    for path in available:
        name = path.rsplit("/", 1)[-1].lower()
        overlap = len(
            set(stem) & set(name)
        )
        scored.append((-overlap, path))
    scored.sort()
    return [path for _score, path in scored[:3]]


def dive(
    repo: Repo, address: str, path: str
) -> tuple[bytes, str]:
    files = repo.files_at(address)
    if path not in files:
        nearest = _closest(path, sorted(files))
        raise Missing(
            f"{path} was not aboard {address[:8]}; "
            "the nearest names there: "
            + ", ".join(nearest)
            + ". The diver deserves the correction, "
            "not an empty net"
        )
    provenance = (
        f"salvaged {path} from {address[:8]} "
        f"({repo.graph.get(address).message.splitlines()[0]!r})"
    )
    return files[path], provenance


def raise_and_commit(
    repo: Repo, address: str, path: str
) -> str:
    content, provenance = dive(repo, address, path)
    current = dict(repo.head_files())
    if current.get(path) == content:
        raise Invalid(
            f"{path} at the tip already matches "
            f"{address[:8]}; a dive after something "
            "already on deck"
        )
    current[path] = content
    landed = repo.commit(current, provenance)
    return (
        f"{provenance}; landed as "
        f"{landed.address[:8]}, and the recovery is "
        "itself history"
    )
