"""Line-range history: follow these lines, not this file.

"When did this function change" is narrower than the file's
history and broader than one line's blame: it is the story of
a range, and the tracker follows it commit by commit walking
backward, adjusting the range as edits above it shift line
numbers, because the function that lives at lines 40 to 60
today lived at 25 to 45 before the imports grew, and a
tracker that forgets to shift reports the wrong neighborhood
with total confidence. A commit enters the story only if its
edit overlaps the range as positioned at that point in
history; edits above merely move the window, edits below are
invisible, and when the range's content stops existing the
walk ends with the birth commit named, which is the answer
archaeology actually wanted.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.difflines import diff_lines
from keel.errors import Invalid, Missing
from keel.repo import Repo


@dataclass(frozen=True)
class RangeEvent:
    address: str
    message: str
    start: int
    end: int


def _shift_range(
    old_text: str,
    new_text: str,
    start: int,
    end: int,
) -> tuple[int, int, bool]:
    hunks = diff_lines(old_text, new_text)
    shift = 0
    touched = False
    for hunk in hunks:
        old_span = len(hunk.old_lines)
        new_span = len(hunk.new_lines)
        hunk_start = hunk.new_start
        hunk_end = hunk.new_start + new_span
        if hunk_end <= start:
            shift += old_span - new_span
        elif hunk_start < end:
            touched = True
    return start + shift, end + shift, touched


def line_history(
    repo: Repo,
    start_commit: str,
    path: str,
    start: int,
    end: int,
) -> list[RangeEvent]:
    if start < 1 or end < start:
        raise Invalid(
            "a range is one-based and ends after it begins"
        )
    files = repo.files_at(start_commit)
    if path not in files:
        raise Missing(f"{path} is not at {start_commit[:8]}")
    events: list[RangeEvent] = []
    cursor: str | None = start_commit
    low, high = start - 1, end
    while cursor is not None:
        commit = repo.graph.get(cursor)
        own = repo.files_at(cursor).get(path)
        if own is None:
            break
        if not commit.parents:
            events.append(
                RangeEvent(
                    address=cursor,
                    message=commit.message,
                    start=low + 1,
                    end=high,
                )
            )
            break
        parent = commit.parents[0]
        parent_content = repo.files_at(parent).get(path)
        if parent_content is None:
            events.append(
                RangeEvent(
                    address=cursor,
                    message=commit.message,
                    start=low + 1,
                    end=high,
                )
            )
            break
        new_low, new_high, touched = _shift_range(
            parent_content.decode(errors="replace"),
            own.decode(errors="replace"),
            low,
            high,
        )
        if touched:
            events.append(
                RangeEvent(
                    address=cursor,
                    message=commit.message,
                    start=low + 1,
                    end=high,
                )
            )
        low, high = new_low, new_high
        cursor = parent
    return events


def narrate_range(
    repo: Repo,
    start_commit: str,
    path: str,
    start: int,
    end: int,
) -> str:
    events = line_history(
        repo, start_commit, path, start, end
    )
    if not events:
        return (
            f"{path}:{start}-{end} was never touched on this "
            "line of history"
        )
    lines = [
        f"{path}:{start}-{end}: {len(events)} event(s), "
        "newest first"
    ]
    for event in events:
        lines.append(
            f"  {event.address[:8]} {event.message} "
            f"(range stood at {event.start}-{event.end})"
        )
    lines.append(
        f"the walk ends at {events[-1].address[:8]}, the "
        "birth, which is the answer archaeology wanted"
    )
    return "\n".join(lines)
