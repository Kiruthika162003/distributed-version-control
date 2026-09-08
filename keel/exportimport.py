"""Fast export and import: history as a stream, for crossing tool boundaries.

Migrations, mirrors, and surgery tools all want history in a
form that is not this system's internals, and the stream
format is that form: commits in topological order, each
carrying its message, its parent references by stream mark
rather than address, and its full file manifest inline. Marks
are the load-bearing idea, small integers standing in for
addresses, because addresses on the importing side will
differ by construction the moment any byte of metadata
differs, and a stream that hardcodes addresses can only
recreate the repository it came from, byte for byte or not at
all. The round trip is the format's honesty test: export then
import must land every commit with the same trees and the
same topology, and the importer verifies parents exist before
using them, since a stream applied out of order builds
orphans with confident faces.
"""

from __future__ import annotations

from keel.errors import Invalid
from keel.repo import Repo


def fast_export(repo: Repo, tip: str) -> str:
    order = sorted(
        repo.graph.ancestors(tip),
        key=lambda address: repo.graph.get(
            address
        ).sequence,
    )
    marks: dict[str, int] = {}
    lines: list[str] = []
    for number, address in enumerate(order, start=1):
        marks[address] = number
        commit = repo.graph.get(address)
        parent_marks = " ".join(
            str(marks[parent])
            for parent in commit.parents
        )
        lines.append(f"commit mark={number}")
        lines.append(f"parents {parent_marks}".rstrip())
        message = commit.message.replace("\n", "\\n")
        lines.append(f"message {message}")
        for path, content in sorted(
            repo.files_at(address).items()
        ):
            body = content.decode(errors="replace").replace(
                "\n", "\\n"
            )
            lines.append(f"file {path} {body}")
        lines.append("end")
    return "\n".join(lines)


def fast_import(stream: str) -> Repo:
    repo = Repo.init()
    marks: dict[int, str] = {}
    current_mark: int | None = None
    parents: tuple[str, ...] = ()
    message = ""
    files: dict[str, bytes] = {}
    for line in stream.splitlines():
        if line.startswith("commit mark="):
            current_mark = int(line.split("=", 1)[1])
            parents = ()
            message = ""
            files = {}
        elif line.startswith("parents"):
            marks_text = line[len("parents") :].split()
            resolved = []
            for mark_text in marks_text:
                mark = int(mark_text)
                if mark not in marks:
                    raise Invalid(
                        f"mark {mark} used before it was "
                        "defined; a stream applied out of "
                        "order builds orphans with confident "
                        "faces"
                    )
                resolved.append(marks[mark])
            parents = tuple(resolved)
        elif line.startswith("message "):
            message = line[len("message ") :].replace(
                "\\n", "\n"
            )
        elif line.startswith("file "):
            _, path, body = line.split(" ", 2)
            files[path] = body.replace("\\n", "\n").encode()
        elif line == "end":
            if current_mark is None:
                raise Invalid("end before any commit began")
            commit = repo.commit_with_parents(
                files, message, parents
            )
            marks[current_mark] = commit.address
            last_address = commit.address
            current_mark = None
        else:
            raise Invalid(
                f"the stream contains {line[:30]!r}, which "
                "this format never emits"
            )
    if marks:
        repo.refs.create_branch("main", last_address)
        repo.refs.checkout("main")
    return repo


def round_trip_verdict(repo: Repo, tip: str) -> str:
    stream = fast_export(repo, tip)
    rebuilt = fast_import(stream)
    original = {
        repo.graph.get(a).tree
        for a in repo.graph.ancestors(tip)
    }
    imported = {
        rebuilt.graph.get(a).tree
        for a in rebuilt.graph.commits
    }
    if original == imported:
        return (
            f"round trip holds: {len(original)} tree(s) "
            "identical on both sides"
        )
    return (
        f"round trip DRIFTED: {len(original - imported)} "
        "tree(s) lost in translation"
    )
