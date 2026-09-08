"""Ignore rules: what history never sees, decided by patterns with a hierarchy.

Build artifacts, editor droppings, and secrets share one
need: the repository must not see them, and must not see them
consistently, because an ignore that works on one machine and
not another turns into a secrets leak with a commit hash. The
matcher supports the grammar people actually use: bare names
matching anywhere, directory patterns with a trailing slash
swallowing everything beneath, star wildcards within a
segment, and negation with a leading bang that re-admits a
path a broader rule excluded, later rules winning, because
"ignore all logs except the one we ship" is the first real
ignore file everyone writes. Every verdict can explain
itself, naming the rule that decided, since debugging an
ignore file without that is guessing at an invisible court.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid


@dataclass(frozen=True)
class Rule:
    pattern: str
    negated: bool
    position: int


def _segment_matches(pattern: str, segment: str) -> bool:
    if "*" not in pattern:
        return pattern == segment
    parts = pattern.split("*")
    if not segment.startswith(parts[0]):
        return False
    if not segment.endswith(parts[-1]):
        return False
    cursor = len(parts[0])
    for middle in parts[1:-1]:
        found = segment.find(middle, cursor)
        if found < 0:
            return False
        cursor = found + len(middle)
    return True


@dataclass
class IgnoreFile:
    rules: list[Rule]

    @classmethod
    def parse(cls, text: str) -> IgnoreFile:
        rules: list[Rule] = []
        for position, raw in enumerate(text.splitlines()):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            negated = line.startswith("!")
            pattern = line[1:] if negated else line
            if not pattern:
                raise Invalid(
                    f"line {position + 1}: a bare bang negates "
                    "nothing"
                )
            rules.append(
                Rule(
                    pattern=pattern,
                    negated=negated,
                    position=position + 1,
                )
            )
        return cls(rules=rules)

    def _rule_hits(self, rule: Rule, path: str) -> bool:
        pattern = rule.pattern
        segments = path.split("/")
        if pattern.endswith("/"):
            wanted = pattern[:-1]
            return any(
                _segment_matches(wanted, segment)
                for segment in segments[:-1]
            )
        if "/" in pattern:
            pattern_segments = pattern.split("/")
            if len(pattern_segments) > len(segments):
                return False
            return all(
                _segment_matches(want, have)
                for want, have in zip(
                    pattern_segments,
                    segments[: len(pattern_segments)],
                    strict=False,
                )
            ) and len(pattern_segments) == len(segments)
        return any(
            _segment_matches(pattern, segment)
            for segment in segments
        )

    def verdict(self, path: str) -> tuple[bool, str]:
        decision = False
        deciding = "no rule matched; tracked by default"
        for rule in self.rules:
            if self._rule_hits(rule, path):
                decision = not rule.negated
                verb = (
                    "re-admitted"
                    if rule.negated
                    else "ignored"
                )
                deciding = (
                    f"{verb} by line {rule.position} "
                    f"({'!' if rule.negated else ''}"
                    f"{rule.pattern})"
                )
        return decision, deciding

    def is_ignored(self, path: str) -> bool:
        decision, _ = self.verdict(path)
        return decision

    def explain(self, path: str) -> str:
        decision, reason = self.verdict(path)
        state = "ignored" if decision else "tracked"
        return f"{path}: {state}; {reason}"
