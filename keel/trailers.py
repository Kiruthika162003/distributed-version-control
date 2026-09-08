"""Message trailers: the structured footer living inside free text.

Commit messages end with a block of key-colon-value lines,
Signed-off-by, Reviewed-by, Fixes, and the block is a real
data channel that survives every transport a commit does,
which no external metadata store can promise. The parser is
strict about where the block lives, contiguous trailer-shaped
lines at the very end separated from the body by a blank
line, because trailer-shaped text quoted in the middle of a
body is prose, and harvesting prose as data is how a
paragraph mentioning Fixes: ends up closing a ticket it was
discussing. Keys normalize to canonical capitalization for
querying while the original text stays untouched, values
keep their whitespace trimmed only at the edges, and adding
a trailer to a message is an append that never reflows the
body, since a tool that rewraps a human's paragraphs to add
one line has misunderstood whose message it is.
"""

from __future__ import annotations

import re

from keel.errors import Invalid

_TRAILER_PATTERN = re.compile(
    r"^([A-Za-z][A-Za-z-]*):\s*(.+)$"
)


def _canonical(key: str) -> str:
    return "-".join(
        part.capitalize() for part in key.split("-")
    )


def parse_trailers(message: str) -> dict[str, list[str]]:
    lines = message.splitlines()
    block: list[tuple[str, str]] = []
    for line in reversed(lines):
        if not line.strip():
            break
        match = _TRAILER_PATTERN.match(line)
        if match is None:
            return {}
        block.append(
            (
                _canonical(match.group(1)),
                match.group(2).strip(),
            )
        )
    if len(block) == len(lines):
        return {}
    found: dict[str, list[str]] = {}
    for key, value in reversed(block):
        found.setdefault(key, []).append(value)
    return found


def add_trailer(
    message: str, key: str, value: str
) -> str:
    if not value.strip():
        raise Invalid(
            f"{key}: an empty trailer value asserts nothing"
        )
    if not re.match(r"^[A-Za-z][A-Za-z-]*$", key):
        raise Invalid(
            f"{key!r} is not a trailer key; letters and "
            "hyphens, starting with a letter"
        )
    canonical = _canonical(key)
    existing = parse_trailers(message)
    line = f"{canonical}: {value.strip()}"
    if existing:
        return message.rstrip("\n") + "\n" + line
    return message.rstrip("\n") + "\n\n" + line


def query(
    message: str, key: str
) -> list[str]:
    return parse_trailers(message).get(_canonical(key), [])


def signoff_chain(message: str) -> str:
    signers = query(message, "signed-off-by")
    if not signers:
        return "no signoffs; the message stands on its own"
    return (
        f"{len(signers)} signoff(s): " + " -> ".join(signers)
    )
