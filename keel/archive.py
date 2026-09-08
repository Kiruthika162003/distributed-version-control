"""Archive: a commit exported as a file listing, byte-stable forever.

Shipping a source release means turning a commit into an
archive, and the only property that matters is determinism:
the same commit must produce the same archive bytes on any
machine in any decade, because release checksums are promises
and a promise that depends on the weather is a liability.
The format here is deliberately boring, sorted paths with
sizes and content digests plus the payload, and everything
that usually breaks determinism is banished by construction:
no timestamps, no owners, no filesystem ordering, no
compression whose level defaults differ across versions. A
prefix folder can wrap the export, the archive digest doubles
as the release checksum, and verify replays the manifest
against the payload so a truncated download fails before it
is unpacked into a build.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from keel.errors import Corrupt, Invalid
from keel.repo import Repo


@dataclass(frozen=True)
class Archive:
    entries: tuple[tuple[str, bytes], ...]

    def manifest(self) -> str:
        lines = []
        for path, content in self.entries:
            digest = hashlib.sha256(content).hexdigest()[:16]
            lines.append(
                f"{path} {len(content)} {digest}"
            )
        return "\n".join(lines)

    def archive_digest(self) -> str:
        folded = hashlib.sha256()
        folded.update(self.manifest().encode())
        for _, content in self.entries:
            folded.update(content)
        return folded.hexdigest()[:20]

    def verify_against(self, sealed_manifest: str) -> str:
        rows: dict[str, tuple[int, str]] = {}
        for row in sealed_manifest.splitlines():
            row_path, size, digest = row.rsplit(" ", 2)
            rows[row_path] = (int(size), digest)
        if set(rows) != {
            path for path, _ in self.entries
        }:
            raise Corrupt(
                "the manifest and the archive disagree about "
                "which files exist; one of them traveled "
                "badly"
            )
        for path, content in self.entries:
            size, digest = rows[path]
            if len(content) != size:
                raise Corrupt(
                    f"{path}: {len(content)} bytes against a "
                    f"manifest of {size}; a truncated "
                    "download fails before it is unpacked "
                    "into a build"
                )
            if (
                hashlib.sha256(content).hexdigest()[:16]
                != digest
            ):
                raise Corrupt(f"{path}: content drifted")
        return (
            f"{len(self.entries)} entrie(s) verified against "
            "the sealed manifest; a manifest recomputed from "
            "the entries it checks would verify its own "
            "tampering"
        )


def export(
    repo: Repo, address: str, prefix: str = ""
) -> Archive:
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    if prefix.startswith("/"):
        raise Invalid("the prefix is a folder name, not a root")
    files = repo.files_at(address)
    entries = tuple(
        (f"{prefix}{path}", content)
        for path, content in sorted(files.items())
    )
    return Archive(entries=entries)


def release_checksum(repo: Repo, address: str) -> str:
    archive = export(repo, address)
    return (
        f"release {address[:8]}: archive digest "
        f"{archive.archive_digest()}; the same commit "
        "produces these bytes on any machine in any decade"
    )
