"""The turnover note: what the next person needs, written by the organs.

Watchkeeping ends with a turnover, and the note that works
is the one the departing person did not have to remember
to write: the situation line first, branch and divergence
and dirt from the prompt's own logic, then the standing
orders in force, because the next person acts under them
whether or not they are mentioned, then what moved lately
from the anchor the reader last saw, and the note closes
with the one free-text line this module accepts, the
human's own sentence, since every organ can say what is
and only the person leaving knows what was almost, the
half-decided thing that the next watch should not have to
rediscover. An empty human sentence is allowed and
recorded as nothing to add, the honest turnover sometimes
being exactly that.
"""

from __future__ import annotations

from keel.catchup import catch_up
from keel.promptline import line as prompt_line
from keel.repo import Repo
from keel.standingorders import board as orders_board


def note(
    repo: Repo,
    last_seen: str,
    handed_by: str,
    sentence: str = "",
    working: dict[str, bytes] | None = None,
    **organ_state,
) -> str:
    sections = [
        f"turnover from {handed_by}:",
        "situation: "
        + prompt_line(repo, working=working),
        orders_board(**organ_state),
        catch_up(repo, last_seen),
    ]
    if sentence.strip():
        sections.append(
            f"in their own words: {sentence.strip()}"
        )
    else:
        sections.append(
            "in their own words: nothing to add, "
            "which is sometimes the honest turnover"
        )
    sections.append(
        "every organ said what is; only the person "
        "leaving knew what was almost"
    )
    return "\n\n".join(sections)
