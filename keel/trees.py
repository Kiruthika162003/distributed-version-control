"""Trees: a directory is the sorted list of what it holds, nothing more.

A tree object serializes its entries in sorted order with kind
and address, which makes two directories equal exactly when
their trees share an address, however deep the nesting. That
is the property every expensive question later reduces to:
"did anything under src/ change" is one comparison, not a
walk. Building from a flat path-to-blob map nests one tree
per directory bottom-up, so an edit deep in the hierarchy
changes only the spine of trees above it, and the store's
deduplication keeps every untouched sibling shared with the
previous snapshot. The diff walks two trees and prunes on
equal addresses, and the pruning is not an optimization but
the point: a version control system that cannot skip identical
subtrees rereads the whole project to learn nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid, Missing
from keel.objects import BLOB, TREE, ObjectStore


def _parse_entries(payload: bytes) -> list[tuple[str, str, str]]:
    entries = []
    for line in payload.decode().splitlines():
        name, kind, address = line.split("\0")
        entries.append((name, kind, address))
    return entries


def _serialize_entries(
    entries: list[tuple[str, str, str]],
) -> bytes:
    lines = [
        f"{name}\0{kind}\0{address}"
        for name, kind, address in sorted(entries)
    ]
    return "\n".join(lines).encode()


@dataclass
class TreeBuilder:
    store: ObjectStore

    def write_tree(self, files: dict[str, str]) -> str:
        for path in files:
            if path.startswith("/") or path.endswith("/"):
                raise Invalid(
                    f"{path!r} has a leading or trailing "
                    "slash; paths are relative and name files"
                )
            if "//" in path or not path:
                raise Invalid(f"{path!r} is not a clean path")
        return self._write_dir(files, prefix="")

    def _write_dir(
        self, files: dict[str, str], prefix: str
    ) -> str:
        entries: list[tuple[str, str, str]] = []
        direct: dict[str, str] = {}
        subdirs: dict[str, dict[str, str]] = {}
        for path, blob in files.items():
            remainder = path[len(prefix) :]
            if "/" in remainder:
                child, _ = remainder.split("/", 1)
                subdirs.setdefault(child, {})[path] = blob
            else:
                direct[remainder] = blob
        overlap = set(direct) & set(subdirs)
        if overlap:
            raise Invalid(
                f"{sorted(overlap)[0]!r} is both a file and a "
                "directory; one name, one nature"
            )
        for name, blob in direct.items():
            entries.append((name, BLOB, blob))
        for name, children in subdirs.items():
            address = self._write_dir(
                children, prefix=f"{prefix}{name}/"
            )
            entries.append((name, TREE, address))
        return self.store.put(TREE, _serialize_entries(entries))

    def read_tree(self, address: str) -> dict[str, str]:
        files: dict[str, str] = {}
        self._read_dir(address, prefix="", into=files)
        return files

    def _read_dir(
        self, address: str, prefix: str, into: dict[str, str]
    ) -> None:
        payload = self.store.get(address, expect=TREE)
        for name, kind, child in _parse_entries(payload):
            if kind == BLOB:
                into[f"{prefix}{name}"] = child
            else:
                self._read_dir(
                    child, prefix=f"{prefix}{name}/", into=into
                )

    def entry_at(self, address: str, path: str) -> str:
        parts = path.split("/")
        current = address
        for depth, part in enumerate(parts):
            payload = self.store.get(current, expect=TREE)
            matches = {
                name: (kind, child)
                for name, kind, child in _parse_entries(payload)
            }
            if part not in matches:
                raise Missing(
                    f"{'/'.join(parts[: depth + 1])} is not in "
                    "this tree"
                )
            kind, current = matches[part]
            if depth < len(parts) - 1 and kind != TREE:
                raise Invalid(
                    f"{'/'.join(parts[: depth + 1])} is a file, "
                    "not a directory"
                )
        return current


def diff_trees(
    builder: TreeBuilder, old: str | None, new: str | None
) -> dict[str, str]:
    if old == new:
        return {}
    old_files = builder.read_tree(old) if old else {}
    new_files = builder.read_tree(new) if new else {}
    changes: dict[str, str] = {}
    for path in sorted(set(old_files) | set(new_files)):
        before = old_files.get(path)
        after = new_files.get(path)
        if before == after:
            continue
        if before is None:
            changes[path] = "added"
        elif after is None:
            changes[path] = "removed"
        else:
            changes[path] = "modified"
    return changes
