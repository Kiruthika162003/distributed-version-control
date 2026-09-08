"""Revision expressions: the little language everyone types without reading.

HEAD~2, release^, v1.0~3, a bare address prefix: revision
expressions are the coordinate system of daily work, and the
grammar here is small and exact. A name resolves through
branches first, then tags, then as an address prefix against
the store, in that order, because names people move outrank
names that hold still outrank raw coordinates, and ambiguity
between a branch and a tag is refused rather than ranked,
since a workspace where v1.0 the branch and v1.0 the tag
disagree is a trap someone armed on purpose or by accident
and either way the tool must not spring it. The suffixes
compose left to right: tilde-n walks n first parents, caret
picks a parent of a merge by number, and walking past the
root names the expression that fell off the world instead of
returning something plausible.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid, Missing
from keel.repo import Repo
from keel.tags import TagStore


@dataclass
class RevParser:
    repo: Repo
    tags: TagStore | None = None

    def _resolve_base(self, name: str) -> str:
        if name == "HEAD":
            return self.repo.refs.current()
        in_branches = name in self.repo.refs.branches
        in_tags = (
            self.tags is not None and name in self.tags.tags
        )
        if in_branches and in_tags:
            raise Invalid(
                f"{name} is both a branch and a tag; a "
                "workspace where they disagree is a trap, and "
                "this tool does not spring traps"
            )
        if in_branches:
            return self.repo.refs.branches[name]
        if in_tags:
            return self.tags.resolve(name)
        matches = [
            address
            for address in self.repo.graph.commits
            if address.startswith(name)
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise Invalid(
                f"{name} matches {len(matches)} commits; a "
                "prefix must name exactly one"
            )
        raise Missing(
            f"{name} is not a branch, a tag, or an address "
            "prefix here"
        )

    def resolve(self, expression: str) -> str:
        if not expression.strip():
            raise Invalid("an empty expression points nowhere")
        index = 0
        while index < len(expression) and (
            expression[index].isalnum()
            or expression[index] in "-_./"
        ):
            index += 1
        base_name = expression[:index]
        if not base_name:
            raise Invalid(
                f"{expression!r} has no base name to resolve"
            )
        address = self._resolve_base(base_name)
        rest = expression[index:]
        cursor = 0
        while cursor < len(rest):
            mark = rest[cursor]
            cursor += 1
            digits = ""
            while (
                cursor < len(rest) and rest[cursor].isdigit()
            ):
                digits += rest[cursor]
                cursor += 1
            count = int(digits) if digits else 1
            if mark == "~":
                for _ in range(count):
                    address = self._first_parent(
                        address, expression
                    )
            elif mark == "^":
                address = self._parent_by_number(
                    address, count, expression
                )
            else:
                raise Invalid(
                    f"{mark!r} is not a suffix this grammar "
                    "knows; tilde and caret compose left to "
                    "right"
                )
        return address

    def _first_parent(
        self, address: str, expression: str
    ) -> str:
        parents = self.repo.graph.get(address).parents
        if not parents:
            raise Missing(
                f"{expression} walks past the root; the "
                "expression fell off the world"
            )
        return parents[0]

    def _parent_by_number(
        self, address: str, number: int, expression: str
    ) -> str:
        parents = self.repo.graph.get(address).parents
        if number < 1 or number > len(parents):
            raise Missing(
                f"{expression} asks for parent {number} of a "
                f"commit with {len(parents)}; merges have "
                "numbered parents and this is not one of them"
            )
        return parents[number - 1]
