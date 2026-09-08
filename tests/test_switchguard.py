from __future__ import annotations

import pytest

from keel.errors import Missing
from keel.repo import Repo
from keel.stash import Stash
from keel.switchguard import switch


def build() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"core\n", "notes.md": b"n\n"},
        "base",
    )
    repo.branch_from_head("feature")
    repo.refs.checkout("feature")
    repo.commit(
        {"app.py": b"core\nfeature\n", "notes.md": b"n\n"},
        "feature diverges app",
    )
    repo.refs.checkout("main")
    return repo


class TestSwitching:
    def test_a_clean_switch_narrates_nothing_extra(self):
        repo = build()
        landed, receipt = switch(
            repo,
            Stash(),
            repo.head_files(),
            "feature",
        )
        assert receipt == "switched to feature"
        assert landed["app.py"] == b"core\nfeature\n"
        assert repo.refs.current_branch() == "feature"

    def test_safe_dirt_travels_with_the_switch(self):
        repo = build()
        working = dict(repo.head_files())
        working["notes.md"] = b"n\nwip thoughts\n"
        landed, receipt = switch(
            repo, Stash(), working, "feature"
        )
        assert "1 dirty path(s) traveled" in receipt
        assert landed["notes.md"] == b"n\nwip thoughts\n"
        assert landed["app.py"] == b"core\nfeature\n"

    def test_endangered_dirt_is_shelved_with_its_story(
        self,
    ):
        repo = build()
        shelf = Stash()
        working = dict(repo.head_files())
        working["app.py"] = b"core\nhalf-done\n"
        working["notes.md"] = b"n\nwip\n"
        landed, receipt = switch(
            repo, shelf, working, "feature"
        )
        assert "shelved app.py" in receipt
        assert (
            "the destination rewrites them"
        ) in receipt
        assert landed["app.py"] == b"core\nfeature\n"
        assert landed["notes.md"] == b"n\nwip\n"
        assert len(shelf.entries) == 1
        assert shelf.entries[0].label == (
            "switch main -> feature shelved these"
        )

    def test_a_ghost_destination_is_refused(self):
        repo = build()
        with pytest.raises(Missing):
            switch(
                repo,
                Stash(),
                repo.head_files(),
                "ghost",
            )
