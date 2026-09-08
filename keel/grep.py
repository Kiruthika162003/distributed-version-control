"""Grep at a commit: search the tree history actually holds, not the disk.

Searching the working copy answers what is here now;
searching a commit answers what the release actually
contained, and the two diverge exactly when it matters, mid
incident, when the deployed artifact came from a commit
three days behind the checkout. The searcher walks a
commit's files, matches line by line, and reports path, line
number, and the line itself, with binary-looking files
skipped and counted rather than searched, because grepping
bytes with no lines produces matches nobody can open. The
cross-commit variant answers the sharper question, which of
these two commits contains the pattern, split into only-in
buckets, since "it greps on my machine" is this domain's
version of the oldest excuse.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid
from keel.repo import Repo


@dataclass(frozen=True)
class GrepHit:
    path: str
    line_number: int
    line: str

    def render(self) -> str:
        return f"{self.path}:{self.line_number}: {self.line}"


def grep_at(
    repo: Repo, address: str, pattern: str
) -> tuple[list[GrepHit], int]:
    if not pattern:
        raise Invalid("an empty pattern matches everything")
    hits: list[GrepHit] = []
    binaries_skipped = 0
    for path, content in sorted(
        repo.files_at(address).items()
    ):
        if b"\x00" in content:
            binaries_skipped += 1
            continue
        for number, line in enumerate(
            content.decode(errors="replace").splitlines(),
            start=1,
        ):
            if pattern in line:
                hits.append(
                    GrepHit(
                        path=path,
                        line_number=number,
                        line=line,
                    )
                )
    return hits, binaries_skipped


def render_grep(
    repo: Repo, address: str, pattern: str
) -> str:
    hits, skipped = grep_at(repo, address, pattern)
    if not hits:
        line = (
            f"{pattern!r} is not in {address[:8]}"
        )
    else:
        line = "\n".join(hit.render() for hit in hits)
    if skipped:
        line += (
            f"\n{skipped} binary file(s) skipped and "
            "counted; matches nobody can open help nobody"
        )
    return line


def grep_between(
    repo: Repo,
    pattern: str,
    old_address: str,
    new_address: str,
) -> str:
    old_hits, _ = grep_at(repo, old_address, pattern)
    new_hits, _ = grep_at(repo, new_address, pattern)
    old_keys = {
        (hit.path, hit.line) for hit in old_hits
    }
    new_keys = {
        (hit.path, hit.line) for hit in new_hits
    }
    only_old = sorted(old_keys - new_keys)
    only_new = sorted(new_keys - old_keys)
    lines = [
        f"{pattern!r}: {len(old_keys & new_keys)} shared, "
        f"{len(only_old)} only in {old_address[:8]}, "
        f"{len(only_new)} only in {new_address[:8]}"
    ]
    for path, text in only_old:
        lines.append(f"  old only: {path}: {text}")
    for path, text in only_new:
        lines.append(f"  new only: {path}: {text}")
    return "\n".join(lines)
