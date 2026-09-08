"""The voyages registry: every example enumerated from its own manifest.

The examples are the workshop's sea trials, each one a day
someone has actually had, and their roster is computed the
way the organs' is: walk the package, read each voyage's
opening docstring line, and refuse to maintain a list that
the filesystem already maintains. The registry also reads
the run instruction out of each docstring, the line that
says python dash m, because an example that cannot tell
you how to run it is a museum piece, and the audit flags
any voyage whose docstring forgot the instruction, the
one clerical standard the fleet is held to. The lobby's
demo verb reads this roster instead of a hand-kept tuple,
which retires the last hardcoded list in the workshop,
and the page says so with the registry's standing boast:
correct by construction, nothing to forget updating.
"""

from __future__ import annotations

import importlib
import pkgutil

import examples


def roster() -> list[tuple[str, str, bool]]:
    found: list[tuple[str, str, bool]] = []
    for info in pkgutil.iter_modules(
        examples.__path__
    ):
        if info.ispkg:
            continue
        module = importlib.import_module(
            f"examples.{info.name}"
        )
        doc = (module.__doc__ or "").strip()
        headline = (
            doc.splitlines()[0]
            if doc
            else "UNDOCUMENTED voyage"
        )
        has_instruction = "python -m examples." in doc
        found.append(
            (info.name, headline, has_instruction)
        )
    return sorted(found)


def names() -> list[str]:
    return [name for name, _headline, _run in roster()]


def page() -> str:
    voyages = roster()
    missing = [
        name
        for name, _headline, has_run in voyages
        if not has_run
    ]
    lines = [
        f"{len(voyages)} voyage(s) on the registry:"
    ]
    lines.extend(
        f"  {name}: {headline}"
        for name, headline, _run in voyages
    )
    if missing:
        lines.append(
            "voyages that forgot their run "
            "instruction: "
            + ", ".join(missing)
            + "; an example that cannot tell you how "
            "to run it is a museum piece"
        )
    else:
        lines.append(
            "every voyage carries its run "
            "instruction; the fleet meets its one "
            "clerical standard"
        )
    lines.append(
        "correct by construction; nothing to forget "
        "updating"
    )
    return "\n".join(lines)
