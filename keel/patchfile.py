"""Patch files: a commit as mail, applied by content rather than by faith.

Before hosting platforms there was mail, and the format
survives because it carries everything a commit is in plain
text: subject, body, and the file changes as old-to-new
pairs. Formatting a commit produces that text; applying it
reconstructs the change on another repository, and the
application is content-checked, each old text must match
what the target holds, path by path, with every mismatch
named before anything is written, because a patch applied
halfway is a working copy nobody can describe. The applied
commit records its origin subject verbatim, and the
round-trip property is the format's contract: format then
apply onto the same base yields a commit whose patch
identity equals the original, provable with the patch id
this repository already trusts for cherry detection.
"""

from __future__ import annotations

from keel.errors import Conflict, Invalid
from keel.repo import Repo


def format_patch(repo: Repo, address: str) -> str:
    commit = repo.graph.get(address)
    if len(commit.parents) != 1:
        raise Invalid(
            "patch mail carries single-parent changes; "
            "merges travel as bundles, not letters"
        )
    parent_files = repo.files_at(commit.parents[0])
    own_files = repo.files_at(address)
    lines = [f"Subject: {commit.message.splitlines()[0]}"]
    body = commit.message.splitlines()[1:]
    for line in body:
        lines.append(f"Body: {line}")
    for path in sorted(set(parent_files) | set(own_files)):
        old = parent_files.get(path)
        new = own_files.get(path)
        if old == new:
            continue
        old_text = (
            old.decode(errors="replace").replace("\n", "\\n")
            if old is not None
            else "<absent>"
        )
        new_text = (
            new.decode(errors="replace").replace("\n", "\\n")
            if new is not None
            else "<absent>"
        )
        lines.append(f"Change: {path}")
        lines.append(f"Old: {old_text}")
        lines.append(f"New: {new_text}")
    return "\n".join(lines)


def apply_patch(repo: Repo, patch_text: str):
    subject = ""
    changes: list[tuple[str, str, str]] = []
    current_path = ""
    current_old = ""
    for line in patch_text.splitlines():
        if line.startswith("Subject: "):
            subject = line[len("Subject: ") :]
        elif line.startswith("Change: "):
            current_path = line[len("Change: ") :]
        elif line.startswith("Old: "):
            current_old = line[len("Old: ") :]
        elif line.startswith("New: "):
            changes.append(
                (
                    current_path,
                    current_old,
                    line[len("New: ") :],
                )
            )
    if not subject:
        raise Invalid("mail without a subject is spam")
    if not changes:
        raise Invalid("mail without changes is a greeting")
    working = dict(repo.head_files())
    mismatches = []
    for path, old_text, _ in changes:
        held = working.get(path)
        expected = (
            None
            if old_text == "<absent>"
            else old_text.replace("\\n", "\n").encode()
        )
        if held != expected:
            mismatches.append(path)
    if mismatches:
        raise Conflict(
            f"the patch does not match the target in "
            f"{', '.join(sorted(mismatches))}; every mismatch "
            "is named before anything is written, because a "
            "patch applied halfway is a working copy nobody "
            "can describe"
        )
    for path, _, new_text in changes:
        if new_text == "<absent>":
            working.pop(path, None)
        else:
            working[path] = new_text.replace(
                "\\n", "\n"
            ).encode()
    return repo.commit(working, subject)
