"""Word diff: inside a changed line, show the words that actually moved.

A line diff calls the whole line changed when one identifier
was renamed, and reviewers pay for that bluntness in
attention: the eye must find the changed word itself, on
every line, all review long. The refinement splits replace
hunks into tokens, words, runs of spaces, and punctuation
each their own token so that renaming a variable does not
claim the operators around it, and re-diffs the token
streams, rendering removals and insertions inline with
brackets. The refinement only fires for replace hunks whose
similarity clears a floor, because word-diffing two unrelated
lines produces confetti that is strictly worse than the
blunt version, and the floor is the difference between a
refinement and a special effect.
"""

from __future__ import annotations

import re

from keel.difflines import Hunk, diff_lines

_TOKEN_PATTERN = re.compile(r"\w+|\s+|[^\w\s]+")
SIMILARITY_FLOOR = 0.4


def tokenize(line: str) -> list[str]:
    return _TOKEN_PATTERN.findall(line)


def _token_similarity(old: str, new: str) -> float:
    old_tokens = [t for t in tokenize(old) if t.strip()]
    new_tokens = [t for t in tokenize(new) if t.strip()]
    if not old_tokens or not new_tokens:
        return 0.0
    pool = list(new_tokens)
    shared = 0
    for token in old_tokens:
        if token in pool:
            pool.remove(token)
            shared += 1
    return 2 * shared / (len(old_tokens) + len(new_tokens))


def word_diff_line(old: str, new: str) -> str:
    old_tokens = tokenize(old)
    new_tokens = tokenize(new)
    old_text = "\n".join(old_tokens)
    new_text = "\n".join(new_tokens)
    hunks = diff_lines(old_text, new_text)
    removed_at: dict[int, list[str]] = {}
    inserted_at: dict[int, list[str]] = {}
    consumed: set[int] = set()
    for hunk in hunks:
        removed_at[hunk.old_start] = list(hunk.old_lines)
        inserted_at[hunk.old_start] = list(hunk.new_lines)
        for offset in range(len(hunk.old_lines)):
            consumed.add(hunk.old_start + offset)
    parts: list[str] = []
    for index in range(len(old_tokens) + 1):
        if index in removed_at or index in inserted_at:
            gone = "".join(removed_at.get(index, []))
            born = "".join(inserted_at.get(index, []))
            if gone.strip():
                parts.append(f"[-{gone}-]")
            if born.strip():
                parts.append(f"{{+{born}+}}")
            if gone and not gone.strip():
                parts.append(gone)
        if index < len(old_tokens) and index not in consumed:
            parts.append(old_tokens[index])
    return "".join(parts)


def refine_hunk(hunk: Hunk) -> list[str]:
    if hunk.kind() != "replace":
        return [
            *(f"-{line}" for line in hunk.old_lines),
            *(f"+{line}" for line in hunk.new_lines),
        ]
    refined: list[str] = []
    pairs = min(len(hunk.old_lines), len(hunk.new_lines))
    for index in range(pairs):
        old = hunk.old_lines[index]
        new = hunk.new_lines[index]
        if _token_similarity(old, new) >= SIMILARITY_FLOOR:
            refined.append(word_diff_line(old, new))
        else:
            refined.append(f"-{old}")
            refined.append(f"+{new}")
    for line in hunk.old_lines[pairs:]:
        refined.append(f"-{line}")
    for line in hunk.new_lines[pairs:]:
        refined.append(f"+{line}")
    return refined
