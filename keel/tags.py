"""Tags: names that do not move, because releases do not un-happen.

A branch is a name that follows work; a tag is a name that
holds still, and the two must not share a mechanism or they
end up sharing failure modes. Tags here are immutable once
placed: retagging a name is refused outright rather than
force-permitted, because a tag that can quietly move makes
"we shipped v2.1" a statement about a moment instead of about
bytes, and every incident review that starts with "which v2.1"
already lost an hour. Annotated tags carry a message and the
address of the commit they seal, deletion exists but is
journaled with the address it abandoned, and listing sorts by
name because tags are looked up, not browsed, and lookup
wants order.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.commits import CommitGraph
from keel.errors import Invalid, Missing


@dataclass(frozen=True)
class Tag:
    name: str
    target: str
    message: str


@dataclass
class TagStore:
    graph: CommitGraph
    tags: dict[str, Tag] = field(default_factory=dict)
    journal: list[str] = field(default_factory=list)

    def place(
        self, name: str, target: str, message: str
    ) -> str:
        if not name.strip() or " " in name:
            raise Invalid(
                f"{name!r} is not a tag name; one word, held "
                "still"
            )
        if name in self.tags:
            raise Invalid(
                f"{name} already seals "
                f"{self.tags[name].target[:8]}; a tag that can "
                "quietly move makes shipped-v2.1 a statement "
                "about a moment instead of about bytes"
            )
        self.graph.get(target)
        if not message.strip():
            raise Invalid(
                "an annotated tag without a message is just "
                "a bookmark wearing a suit"
            )
        self.tags[name] = Tag(
            name=name, target=target, message=message
        )
        self.journal.append(
            f"tag {name} sealed {target[:8]}: {message}"
        )
        return f"{name} seals {target[:8]}"

    def resolve(self, name: str) -> str:
        tag = self.tags.get(name)
        if tag is None:
            raise Missing(f"{name} is not a tag")
        return tag.target

    def delete(self, name: str) -> str:
        tag = self.tags.pop(name, None)
        if tag is None:
            raise Missing(f"{name} is not a tag")
        self.journal.append(
            f"tag {name} deleted, abandoning "
            f"{tag.target[:8]}"
        )
        return (
            f"{name} deleted; the journal keeps the address "
            "it abandoned"
        )

    def listing(self) -> list[str]:
        return [
            f"{tag.name} -> {tag.target[:8]} ({tag.message})"
            for tag in sorted(
                self.tags.values(),
                key=lambda held: held.name,
            )
        ]

    def describe(self, address: str) -> str:
        exact = [
            tag.name
            for tag in self.tags.values()
            if tag.target == address
        ]
        if exact:
            return f"exactly {sorted(exact)[0]}"
        reachable = [
            (
                self.graph.get(address).sequence
                - self.graph.get(tag.target).sequence,
                tag.name,
            )
            for tag in self.tags.values()
            if self.graph.is_ancestor(tag.target, address)
        ]
        if not reachable:
            return "no tag reaches this commit"
        distance, name = min(reachable)
        return f"{name} plus {distance} commit(s)"
