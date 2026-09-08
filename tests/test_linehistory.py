from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.linehistory import line_history, narrate_range
from keel.repo import Repo


def storied() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"def target():\n    return 1"},
        "birth",
    )
    repo.commit(
        {
            "app.py": (
                b"import os\nimport sys\n"
                b"def target():\n    return 1"
            )
        },
        "imports grew above",
    )
    repo.commit(
        {
            "app.py": (
                b"import os\nimport sys\n"
                b"def target():\n    return 2"
            )
        },
        "the body changed",
    )
    repo.commit(
        {
            "app.py": (
                b"import os\nimport sys\n"
                b"def target():\n    return 2\n"
                b"def other():\n    pass"
            )
        },
        "unrelated below",
    )
    return repo


class TestTheWalk:
    def test_edits_above_shift_and_do_not_star(self):
        repo = storied()
        events = line_history(
            repo, repo.refs.current(), "app.py", 3, 4
        )
        messages = [event.message for event in events]
        assert "imports grew above" not in messages
        assert "the body changed" in messages
        assert messages[-1] == "birth"

    def test_edits_below_are_invisible(self):
        repo = storied()
        events = line_history(
            repo, repo.refs.current(), "app.py", 3, 4
        )
        assert "unrelated below" not in [
            event.message for event in events
        ]

    def test_the_range_position_travels_with_the_story(self):
        repo = storied()
        events = line_history(
            repo, repo.refs.current(), "app.py", 3, 4
        )
        birth = events[-1]
        assert (birth.start, birth.end) == (1, 2)

    def test_the_walk_ends_at_the_birth(self):
        repo = storied()
        story = narrate_range(
            repo, repo.refs.current(), "app.py", 3, 4
        )
        assert "the birth, which is the answer" in story


class TestRefusals:
    def test_ranges_are_one_based_and_ordered(self):
        repo = storied()
        with pytest.raises(Invalid):
            line_history(
                repo, repo.refs.current(), "app.py", 0, 4
            )
        with pytest.raises(Invalid):
            line_history(
                repo, repo.refs.current(), "app.py", 5, 2
            )

    def test_the_absent_path_is_missing(self):
        repo = storied()
        with pytest.raises(Missing):
            line_history(
                repo, repo.refs.current(), "ghost.py", 1, 2
            )
