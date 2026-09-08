"""Ignore rules: what the repository refuses to notice, written down.

Build outputs, editor droppings, and local secrets must
never become history, and the ignore file is that refusal
made durable. The grammar is small and its edges are where
every implementation earns its scars: a pattern matches
basenames anywhere unless it contains a slash, which anchors
it to the root; a trailing slash matches directories and
everything under them; leading exclamation re-includes what
an earlier rule excluded, and order matters because the last
matching rule wins. The explain call is the half tools skip:
given a path, it names the rule that decided and the rules
that were overridden, because "why is my file ignored" is
asked daily in every shop and grepping patterns by eye is
how it stays asked. Tracked files are never ignored
retroactively, the rules gate arrivals, not residents.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field

from keel.errors import Invalid


@dataclass(frozen=True)
class Rule:
    position: int
    pattern: str
    negated: bool

    def matches(self, path: str) -> bool:
        pattern = self.pattern
        if pattern.endswith("/"):
            prefix = pattern.rstrip("/")
            if "/" not in prefix:
                parts = path.split("/")
                return prefix in parts[:-1]
            return path.startswith(prefix + "/")
        if "/" in pattern:
            return fnmatch.fnmatch(path, pattern)
        basename = path.rsplit("/", 1)[-1]
        return fnmatch.fnmatch(basename, pattern)


@dataclass
class IgnoreRules:
    rules: list[Rule] = field(default_factory=list)

    @classmethod
    def parse(cls, text: str) -> IgnoreRules:
        rules: list[Rule] = []
        for position, raw in enumerate(
            text.splitlines(), start=1
        ):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            negated = line.startswith("!")
            pattern = line[1:] if negated else line
            if not pattern:
                raise Invalid(
                    f"line {position}: a bare exclamation "
                    "un-ignores nothing"
                )
            rules.append(
                Rule(
                    position=position,
                    pattern=pattern,
                    negated=negated,
                )
            )
        return cls(rules=rules)

    def decides(self, path: str) -> Rule | None:
        decider: Rule | None = None
        for rule in self.rules:
            if rule.matches(path):
                decider = rule
        return decider

    def is_ignored(self, path: str) -> bool:
        decider = self.decides(path)
        return decider is not None and not decider.negated

    def explain(self, path: str) -> str:
        matching = [
            rule
            for rule in self.rules
            if rule.matches(path)
        ]
        if not matching:
            return (
                f"{path}: no rule speaks; the file arrives "
                "freely"
            )
        decider = matching[-1]
        verdict = (
            "re-included" if decider.negated else "ignored"
        )
        lines = [
            f"{path}: {verdict} by line "
            f"{decider.position} ({decider.pattern})"
        ]
        for overridden in matching[:-1]:
            lines.append(
                f"  overrides line {overridden.position} "
                f"({overridden.pattern}); the last matching "
                "rule wins"
            )
        return "\n".join(lines)

    def gate_arrivals(
        self,
        candidate_files: dict[str, bytes],
        tracked: set[str],
    ) -> tuple[dict[str, bytes], list[str]]:
        admitted: dict[str, bytes] = {}
        refused: list[str] = []
        for path, content in candidate_files.items():
            if path in tracked or not self.is_ignored(path):
                admitted[path] = content
            else:
                refused.append(path)
        return admitted, sorted(refused)
