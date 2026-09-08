from __future__ import annotations

import pytest

from keel.errors import Missing
from keel.followpath import follow, narrate
from keel.repo import Repo


def build() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"utils.py": b"helpers\n"}, "birth as utils"
    )
    repo.commit(
        {"utils.py": b"helpers\nmore\n"}, "grow utils"
    )
    repo.commit(
        {"toolbox.py": b"helpers\nmore\n"},
        "rename to toolbox",
    )
    repo.commit(
        {"kit.py": b"helpers\nmore\nedited\n"},
        "rename to kit with edits",
    )
    repo.commit(
        {"kit.py": b"helpers\nmore\nedited\nfinal\n"},
        "polish kit",
    )
    return repo


class TestTheTrail:
    def test_every_name_and_jump_is_recorded(self):
        repo = build()
        trail = follow(
            repo, repo.refs.current(), "kit.py"
        )
        notes = [step.note for step in trail]
        assert notes[0] == "edited"
        assert notes[1].startswith(
            "renamed from toolbox.py (80% similar"
        )
        assert "the one weak link" in notes[1]
        assert notes[2] == (
            "renamed from utils.py (exact content)"
        )
        assert notes[3] == "edited"
        assert notes[4] == (
            "born here; a birth is a birth"
        )

    def test_the_headline_chains_the_names(self):
        repo = build()
        page = narrate(
            repo, repo.refs.current(), "kit.py"
        )
        assert page.startswith(
            "kit.py has answered to 3 name(s): "
            "kit.py <- toolbox.py <- utils.py"
        )

    def test_a_true_birth_ends_the_trail_plainly(self):
        repo = Repo.init()
        repo.commit({"a.py": b"a\n"}, "start")
        repo.commit(
            {"a.py": b"a\n", "brand.py": b"new\n"},
            "brand arrives fresh",
        )
        trail = follow(
            repo, repo.refs.current(), "brand.py"
        )
        assert trail[0].note == (
            "appeared with no candidate above the "
            "floor; a birth is a birth"
        )

    def test_following_a_ghost_is_refused(self):
        repo = build()
        with pytest.raises(Missing):
            follow(repo, repo.refs.current(), "ghost.py")
