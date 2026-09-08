"""The organ registry: a table of contents that cannot go stale.

Hand-written module lists rot the day after they are
written, so the registry walks the package and reads each
organ's own first docstring line, the sentence every module
here opens with, and the roster is therefore correct by
construction: adding an organ adds its row, renaming one
renames it, and deleting one deletes it, with no list to
forget updating. The page doubles as a quality gate in the
repository's own spirit, an organ with no docstring is
listed as undocumented and counted in the headline, because
a nameless organ in a codebase built on narration is a
finding, not a formatting preference. The lobby lists the
rooms and not itself, and the witnesses wing is listed as
one door, since its residents introduce themselves through
their own registry.
"""

from __future__ import annotations

import importlib
import pkgutil

import keel

EXCLUDED = ("cli", "organs")


def roster() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for info in pkgutil.iter_modules(keel.__path__):
        if info.ispkg or info.name in EXCLUDED:
            continue
        module = importlib.import_module(
            f"keel.{info.name}"
        )
        doc = (module.__doc__ or "").strip()
        headline = (
            doc.splitlines()[0]
            if doc
            else "UNDOCUMENTED; a nameless organ is a "
            "finding, not a formatting preference"
        )
        found.append((info.name, headline))
    return sorted(found)


def page() -> str:
    organs = roster()
    nameless = sum(
        1
        for _name, headline in organs
        if headline.startswith("UNDOCUMENTED")
    )
    lines = [
        f"{len(organs)} organ(s), {nameless} "
        "undocumented:"
    ]
    lines.extend(
        f"  {name}: {headline}"
        for name, headline in organs
    )
    lines.append(
        "correct by construction; there is no list "
        "to forget updating"
    )
    return "\n".join(lines)
