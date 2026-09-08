"""Attributes: per-path declarations, checked at parse and settled per key.

Attributes answer questions other machinery asks: which
line endings a path normalizes to, whether it is binary and
therefore beyond line tools, whether it ships in archives,
which merge driver adjudicates it. The file is declarations
and declarations get checked at parse time: an unknown
attribute is refused with the known four listed, eol only
accepts lf or crlf, binary takes no value because a flag
with a value is two features wearing one name, and merge
without a driver names nothing. Resolution is later-wins
per attribute key rather than per line, so a broad rule can
set eol for the tree while a narrow rule flips one path's
merge driver without re-stating the eol it never disagreed
with. The explain answer always names the line that decided
or says unset plainly, because attribute debugging is
archaeology and archaeology needs strata, not verdicts.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field

from keel.errors import Invalid

KNOWN = ("eol", "binary", "export-ignore", "merge")
EOL_VALUES = ("lf", "crlf")


@dataclass(frozen=True)
class AttributeRule:
    position: int
    pattern: str
    settings: tuple[tuple[str, str], ...]

    def matches(self, path: str) -> bool:
        if self.pattern.endswith("/"):
            return path.startswith(self.pattern)
        return fnmatch.fnmatch(path, self.pattern)


def _check_setting(
    position: int, key: str, value: str, flagged: bool
) -> None:
    if key not in KNOWN:
        raise Invalid(
            f"line {position}: {key} is not an "
            f"attribute; the known four are "
            f"{', '.join(KNOWN)}"
        )
    if key == "binary" and flagged:
        raise Invalid(
            f"line {position}: binary takes no value; a "
            "flag with a value is two features wearing "
            "one name"
        )
    if key == "eol" and value not in EOL_VALUES:
        raise Invalid(
            f"line {position}: eol accepts lf or crlf, "
            f"not {value!r}"
        )
    if key == "merge" and not value:
        raise Invalid(
            f"line {position}: merge without a driver "
            "names nothing"
        )


@dataclass
class AttributesFile:
    rules: list[AttributeRule] = field(default_factory=list)

    @classmethod
    def parse(cls, text: str) -> AttributesFile:
        rules: list[AttributeRule] = []
        for position, raw in enumerate(
            text.splitlines(), start=1
        ):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                raise Invalid(
                    f"line {position}: a pattern with no "
                    "attributes declares nothing"
                )
            settings = []
            for token in parts[1:]:
                key, flagged, value = token.partition("=")
                _check_setting(
                    position, key, value, bool(flagged)
                )
                settings.append((key, value or "set"))
            rules.append(
                AttributeRule(
                    position=position,
                    pattern=parts[0],
                    settings=tuple(settings),
                )
            )
        return cls(rules=rules)

    def lookup(self, path: str) -> dict[str, str]:
        found: dict[str, str] = {}
        for rule in self.rules:
            if rule.matches(path):
                for key, value in rule.settings:
                    found[key] = value
        return found

    def explain(self, path: str, key: str) -> str:
        decider: AttributeRule | None = None
        value = ""
        for rule in self.rules:
            if rule.matches(path):
                for held_key, held_value in rule.settings:
                    if held_key == key:
                        decider = rule
                        value = held_value
        if decider is None:
            return (
                f"{path}: {key} unset; the default is "
                "the absence, not a hidden rule"
            )
        return (
            f"{path}: {key}={value}, decided by line "
            f"{decider.position} ({decider.pattern})"
        )

    def merge_driver(self, path: str) -> str:
        return self.lookup(path).get("merge", "diff3")

    def is_binary(self, path: str) -> bool:
        return "binary" in self.lookup(path)

    def export_paths(
        self, paths: list[str]
    ) -> tuple[list[str], list[str]]:
        shipped = []
        held_back = []
        for path in sorted(paths):
            if "export-ignore" in self.lookup(path):
                held_back.append(path)
            else:
                shipped.append(path)
        return shipped, held_back
