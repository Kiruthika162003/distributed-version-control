"""Pretty log: a template language small enough to refuse to guess.

A log formatter is a contract between the template and the
reader, and the placeholders here honor it strictly: %H is
the full address, %h the short one, %s the subject line, %b
the body below it, %p the short parents, %n the repository
sequence number, %d the decorations, and %% a literal
percent. An unknown placeholder is refused with its position
named rather than passed through or silently dropped,
because a formatter that guesses turns a typo in a script
into a column of garbage that ships to whoever reads the
report. Decorations are computed from the ref table and the
tag store at format time, never cached, since a decoration
is a claim about where names point right now, and stale
claims about names are how people delete the wrong branch.
The subject-body split follows the oldest convention in the
log: the first line is the headline and the rest is the
story, and templates can ask for either without getting both.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.commits import Commit
from keel.errors import Invalid
from keel.repo import Repo
from keel.tags import TagStore

KNOWN = "Hhsbpnd%"
ONELINE = "%h %d%s"


def subject_of(message: str) -> str:
    return message.splitlines()[0] if message else ""


def body_of(message: str) -> str:
    lines = message.splitlines()[1:]
    while lines and not lines[0].strip():
        lines = lines[1:]
    return "\n".join(lines)


@dataclass
class Decorator:
    repo: Repo
    tags: TagStore | None = None

    def names_at(self, address: str) -> list[str]:
        names = [
            branch
            for branch, tip in sorted(
                self.repo.refs.branches.items()
            )
            if tip == address
        ]
        if self.tags is not None:
            names.extend(
                f"tag: {name}"
                for name, tag in sorted(
                    self.tags.tags.items()
                )
                if tag.target == address
            )
        return names

    def render(self, address: str) -> str:
        names = self.names_at(address)
        if not names:
            return ""
        return f"({', '.join(names)}) "


def format_commit(
    commit: Commit,
    template: str,
    decorator: Decorator | None = None,
) -> str:
    pieces: list[str] = []
    index = 0
    length = len(template)
    while index < length:
        char = template[index]
        if char != "%":
            pieces.append(char)
            index += 1
            continue
        if index + 1 >= length:
            raise Invalid(
                f"the template ends mid-placeholder at "
                f"position {index}"
            )
        code = template[index + 1]
        if code not in KNOWN:
            raise Invalid(
                f"%{code} at position {index} is not a "
                "placeholder; a formatter that guesses "
                "ships garbage to whoever reads the report"
            )
        if code == "%":
            pieces.append("%")
        elif code == "H":
            pieces.append(commit.address)
        elif code == "h":
            pieces.append(commit.address[:8])
        elif code == "s":
            pieces.append(subject_of(commit.message))
        elif code == "b":
            pieces.append(body_of(commit.message))
        elif code == "p":
            pieces.append(
                " ".join(p[:8] for p in commit.parents)
            )
        elif code == "n":
            pieces.append(str(commit.sequence))
        elif code == "d":
            rendered = ""
            if decorator is not None:
                rendered = decorator.render(commit.address)
            pieces.append(rendered)
        index += 2
    return "".join(pieces)


def pretty_log(
    repo: Repo,
    template: str = ONELINE,
    tags: TagStore | None = None,
    limit: int | None = None,
) -> str:
    if limit is not None and limit < 1:
        raise Invalid(
            "a log limited to zero entries is silence "
            "wearing a formatter"
        )
    decorator = Decorator(repo=repo, tags=tags)
    commits = repo.graph.log(repo.refs.current())
    if limit is not None:
        commits = commits[:limit]
    return "\n".join(
        format_commit(commit, template, decorator)
        for commit in commits
    )
