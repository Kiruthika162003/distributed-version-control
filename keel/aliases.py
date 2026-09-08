"""Aliases: shorthand that expands in the open and never eats a real verb.

An alias is a private dialect, and dialects go wrong in two
known ways this table refuses at definition time. Shadowing
a built-in verb is refused outright, because the day someone
aliases push to pull is the day muscle memory becomes an
incident, and no expansion is worth a homonym for a real
command. Cycles are refused at definition rather than
discovered at expansion, walking the chain the moment an
alias is added, since the shell that hangs expanding a
around b around a is debugging somebody's joke. Expansion
itself is transparent by contract: the result names every
hop it took, s becoming status becoming report, because an
alias that expands silently is a prank on whoever reads the
transcript, and transcripts get read at exactly the moments
nobody enjoys.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing

BUILTINS = (
    "commit",
    "branch",
    "merge",
    "rebase",
    "push",
    "fetch",
    "log",
    "diff",
    "stash",
    "bisect",
    "tag",
    "blame",
)


@dataclass
class AliasTable:
    entries: dict[str, str] = field(default_factory=dict)

    def define(self, name: str, expansion: str) -> str:
        if not name.strip() or " " in name:
            raise Invalid(
                f"{name!r} is not an alias name; one word"
            )
        if name in BUILTINS:
            raise Invalid(
                f"{name} is a real verb; the day someone "
                "aliases push to pull is the day muscle "
                "memory becomes an incident"
            )
        words = expansion.split()
        head = words[0] if words else ""
        if not head:
            raise Invalid(
                f"{name} expands to nothing; silence is "
                "not a command"
            )
        self.entries[name] = expansion
        try:
            self.expand(name)
        except Invalid:
            del self.entries[name]
            raise
        return f"{name} -> {expansion}"

    def remove(self, name: str) -> str:
        if name not in self.entries:
            raise Missing(f"{name} is not an alias")
        del self.entries[name]
        return f"{name} forgotten"

    def expand(self, command: str) -> str:
        words = command.split()
        head = words[0]
        rest = words[1:]
        hops = [head]
        while head in self.entries:
            expansion = self.entries[head].split()
            head = expansion[0]
            rest = expansion[1:] + rest
            if head in hops:
                chain = " -> ".join([*hops, head])
                raise Invalid(
                    f"alias cycle: {chain}; the shell "
                    "that hangs expanding this is "
                    "debugging somebody's joke"
                )
            hops.append(head)
        final = " ".join([head, *rest]).strip()
        if len(hops) == 1:
            return final
        trail = " -> ".join(hops)
        return f"{final}  [{trail}]"

    def listing(self) -> str:
        if not self.entries:
            return "no aliases; everyone speaks standard"
        lines = [f"{len(self.entries)} alias(es):"]
        lines.extend(
            f"  {name} -> {self.entries[name]}"
            for name in sorted(self.entries)
        )
        return "\n".join(lines)
