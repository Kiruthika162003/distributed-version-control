"""Hooks: the repository's immune system, with a strict sense of jurisdiction.

Hooks run other people's judgment at fixed moments, before a
commit lands, before a push leaves, and the design questions
are all about power: a pre-commit hook may reject with a
reason, never rewrite, because a hook that silently fixes
what it dislikes trains developers to commit without
looking; a pre-push hook sees the tip it is vouching for and
its verdict travels with the refusal so the pusher knows
which guard said no and why. Hooks run in registration order
and the first rejection stops the line, since running the
rest wastes their time on a doomed candidate, but every
skipped hook is named in the refusal, because "rejected by
lint, three guards unheard" tells the developer exactly how
much gauntlet remains. A hook that throws instead of voting
is a broken guard, and broken guards fail the operation
loudly rather than waving it through, the only safe default
a gate can have.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from keel.errors import Invalid

Verdict = tuple[bool, str]
Hook = Callable[[dict[str, bytes], str], Verdict]


@dataclass
class HookRunner:
    hooks: list[tuple[str, Hook]] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)

    def register(self, name: str, hook: Hook) -> str:
        if any(held == name for held, _ in self.hooks):
            raise Invalid(
                f"{name} is already registered; two guards "
                "with one name answer for each other's "
                "mistakes"
            )
        self.hooks.append((name, hook))
        return f"guard {name} posted"

    def run(
        self, files: dict[str, bytes], message: str
    ) -> str:
        for position, (name, hook) in enumerate(self.hooks):
            try:
                passed, reason = hook(files, message)
            except Exception as error:
                raise Invalid(
                    f"guard {name} threw ({error}); a broken "
                    "guard fails the gate loudly rather than "
                    "waving it through"
                ) from error
            if not passed:
                unheard = [
                    later
                    for later, _ in self.hooks[position + 1 :]
                ]
                refusal = (
                    f"rejected by {name}: {reason}"
                    + (
                        f"; {len(unheard)} guard(s) unheard "
                        f"({', '.join(unheard)})"
                        if unheard
                        else ""
                    )
                )
                self.refusals.append(refusal)
                raise Invalid(refusal)
        return (
            f"{len(self.hooks)} guard(s) satisfied; the gate "
            "opens"
        )


def no_debug_droppings(
    files: dict[str, bytes], message: str
) -> Verdict:
    del message
    for path, content in sorted(files.items()):
        if b"breakpoint()" in content:
            return (
                False,
                f"{path} carries a breakpoint(); nobody "
                "means to ship those",
            )
    return True, "no droppings"


def message_says_something(
    files: dict[str, bytes], message: str
) -> Verdict:
    del files
    first_line = message.splitlines()[0] if message else ""
    if len(first_line) < 10:
        return (
            False,
            f"the subject {first_line!r} is "
            f"{len(first_line)} character(s); history "
            "deserves a sentence",
        )
    if len(first_line) > 72:
        return (
            False,
            "the subject runs past 72 characters; the rest "
            "belongs in the body",
        )
    return True, "the message says something"


def no_giant_files(
    files: dict[str, bytes], message: str
) -> Verdict:
    del message
    for path, content in sorted(files.items()):
        if len(content) > 100_000:
            return (
                False,
                f"{path} is {len(content)} bytes; history "
                "remembers forever, so large blobs need a "
                "pointer store, not a commit",
            )
    return True, "no giants"
