"""Changelog generation: the release notes are computed, then edited.

Hand-written release notes drift from reality in both
directions, listing work that slipped and omitting work that
landed, so the draft is computed from the commits between two
tags and the human's job shrinks to editing prose rather
than reconstructing facts. Commits classify by their subject
prefix into the sections readers expect, fixes, features,
and the breaking bucket that must never be buried, with the
unclassified remainder shown under its own honest heading
rather than deleted, because a changelog that silently drops
what it cannot categorize teaches authors to stop reading
it. Merge commits are folded out by default since they
narrate the plumbing rather than the change, and every entry
keeps its short address, so a curious reader is one lookup
from the whole story.
"""

from __future__ import annotations

from keel.errors import Invalid
from keel.repo import Repo

SECTIONS = (
    ("breaking", ("breaking:", "break:")),
    ("features", ("feat:", "feature:", "add:")),
    ("fixes", ("fix:", "bugfix:")),
)


def _classify(message: str) -> str:
    lowered = message.lower()
    for section, prefixes in SECTIONS:
        if lowered.startswith(prefixes):
            return section
    return "uncategorized"


def _strip_prefix(message: str) -> str:
    for _, prefixes in SECTIONS:
        for prefix in prefixes:
            if message.lower().startswith(prefix):
                return message[len(prefix) :].strip()
    return message


def changelog_between(
    repo: Repo, old_tip: str, new_tip: str
) -> dict[str, list[str]]:
    fresh = repo.graph.ancestors(
        new_tip
    ) - repo.graph.ancestors(old_tip)
    if not fresh:
        raise Invalid(
            "nothing landed between these points; a "
            "changelog of nothing is a shrug with headings"
        )
    sections: dict[str, list[str]] = {
        "breaking": [],
        "features": [],
        "fixes": [],
        "uncategorized": [],
    }
    ordered = sorted(
        fresh,
        key=lambda address: -repo.graph.get(
            address
        ).sequence,
    )
    for address in ordered:
        commit = repo.graph.get(address)
        if len(commit.parents) > 1:
            continue
        section = _classify(commit.message)
        sections[section].append(
            f"{_strip_prefix(commit.message)} "
            f"({address[:8]})"
        )
    return sections


def render_changelog(
    repo: Repo,
    old_tip: str,
    new_tip: str,
    version: str,
) -> str:
    sections = changelog_between(repo, old_tip, new_tip)
    lines = [f"{version}"]
    titles = {
        "breaking": "Breaking changes, never buried",
        "features": "Features",
        "fixes": "Fixes",
        "uncategorized": (
            "Uncategorized, shown rather than dropped"
        ),
    }
    for key in (
        "breaking",
        "features",
        "fixes",
        "uncategorized",
    ):
        entries = sections[key]
        if not entries:
            continue
        lines.append(f"## {titles[key]}")
        lines.extend(f"- {entry}" for entry in entries)
    lines.append(
        "computed draft; the human edits prose, not facts"
    )
    return "\n".join(lines)
