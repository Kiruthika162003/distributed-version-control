"""Path style: the tree's naming habits, inventoried and gently compared.

A tree develops naming habits the way a team develops a
voice, and the audit reads them without legislating: the
extension inventory first, because the census that says
four kinds of config file live here is the beginning of
every consolidation conversation, then the case styles per
directory, snake and kebab and camel counted where they
live, since a directory that mixes styles is not wrong but
is asking every newcomer to guess, and the audit flags
only the mix, never the choice. Extensionless files are
their own column rather than an error, the Makefile and
the LICENSE being citizens in good standing, and the one
hard finding is reserved for the invisible: names that
begin or end with whitespace or contain control
characters, which are not a style but a prank on every
shell that ever touches them.
"""

from __future__ import annotations

import re

from keel.repo import Repo

SNAKE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)+$")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)+$")
CAMEL = re.compile(r"^[a-z]+([A-Z][a-z0-9]*)+$")


def _style(stem: str) -> str:
    if SNAKE.match(stem):
        return "snake"
    if KEBAB.match(stem):
        return "kebab"
    if CAMEL.match(stem):
        return "camel"
    return "plain"


def audit(repo: Repo, address: str) -> str:
    paths = sorted(repo.files_at(address))
    extensions: dict[str, int] = {}
    styles_by_dir: dict[str, set[str]] = {}
    pranks: list[str] = []
    for path in paths:
        name = path.rsplit("/", 1)[-1]
        directory = (
            path.rsplit("/", 1)[0]
            if "/" in path
            else "(root)"
        )
        if name != name.strip() or any(
            ord(char) < 32 for char in name
        ):
            pranks.append(
                f"  invisible: {path!r}; not a style, "
                "a prank on every shell that touches it"
            )
        if "." in name and not name.startswith("."):
            extension = name.rsplit(".", 1)[-1]
            stem = name.rsplit(".", 1)[0]
        else:
            extension = "(none)"
            stem = name
        extensions[extension] = (
            extensions.get(extension, 0) + 1
        )
        found = _style(stem)
        if found != "plain":
            styles_by_dir.setdefault(
                directory, set()
            ).add(found)
    lines = [
        f"naming habits across {len(paths)} path(s):"
    ]
    for extension in sorted(
        extensions,
        key=lambda held: (-extensions[held], held),
    ):
        lines.append(
            f"  .{extension}: {extensions[extension]}"
            if extension != "(none)"
            else (
                f"  extensionless: "
                f"{extensions[extension]}, citizens "
                "in good standing"
            )
        )
    for directory in sorted(styles_by_dir):
        styles = sorted(styles_by_dir[directory])
        if len(styles) > 1:
            lines.append(
                f"  mixed styles in {directory}: "
                + " and ".join(styles)
                + "; not wrong, but asking every "
                "newcomer to guess"
            )
    lines.extend(pranks)
    if len(lines) == 1 + len(extensions):
        lines.append(
            "one style per room and nothing "
            "invisible; the habits are habits"
        )
    return "\n".join(lines)
