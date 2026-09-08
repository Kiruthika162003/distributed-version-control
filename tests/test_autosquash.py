from __future__ import annotations

import pytest

from keel.autosquash import plan
from keel.errors import Invalid
from keel.rebaseplan import execute
from keel.repo import Repo

BASE = {"readme.md": b"hello project\n"}


def build() -> tuple[Repo, str, str]:
    repo = Repo.init()
    ground = repo.commit(dict(BASE), "ground")
    repo.commit(
        dict(BASE, **{"a.py": b"hello\n"}), "add greeting"
    )
    repo.commit(
        dict(
            BASE,
            **{"a.py": b"hello\n", "conf.ini": b"x=1\n"},
        ),
        "add config",
    )
    repo.commit(
        dict(
            BASE,
            **{
                "a.py": b"hello world\n",
                "conf.ini": b"x=1\n",
            },
        ),
        "fixup! add greeting",
    )
    tip = repo.commit(
        dict(
            BASE,
            **{
                "a.py": b"hello world\n",
                "conf.ini": b"x=1\ny=2\n",
            },
        ),
        "squash! add config",
    )
    return repo, ground.address, tip.address


class TestThePlan:
    def test_amendments_jump_behind_their_targets(self):
        repo, base, tip = build()
        page = plan(repo, base, tip)
        lines = page.splitlines()
        assert lines[0].endswith("add greeting")
        assert lines[1].startswith("fixup ")
        assert lines[1].endswith("fixup! add greeting")
        assert lines[2].endswith("add config")
        assert lines[3].startswith("squash ")

    def test_prefix_matches_count(self):
        repo, base, _tip = build()
        orphan = repo.commit(
            dict(
                BASE,
                **{
                    "a.py": b"hello world!\n",
                    "conf.ini": b"x=1\ny=2\n",
                },
            ),
            "fixup! add gr",
        )
        page = plan(repo, base, orphan.address)
        lines = page.splitlines()
        assert lines[1].endswith("fixup! add greeting")
        assert lines[2].endswith("fixup! add gr")

    def test_an_aimless_fixup_gets_the_roster(self):
        repo, base, _tip = build()
        stray = repo.commit(
            dict(
                BASE,
                **{
                    "a.py": b"hello world\n",
                    "conf.ini": b"x=1\ny=2\nz=3\n",
                },
            ),
            "fixup! polish the docs",
        )
        with pytest.raises(Invalid) as caught:
            plan(repo, base, stray.address)
        message = str(caught.value)
        assert "aimed at 'polish the docs'" in message
        assert "'add greeting'" in message
        assert "land on strangers" in message


class TestEndToEnd:
    def test_the_plan_executes_into_two_clean_commits(
        self,
    ):
        repo, base, tip = build()
        result = execute(
            repo, base, tip, plan(repo, base, tip)
        )
        landed = {
            entry.new_address
            for entry in result.entries
            if entry.new_address is not None
        }
        assert len(landed) == 2
        tip_commit = repo.graph.get(result.new_tip)
        assert tip_commit.message == (
            "add config\n\nsquash! add config"
        )
        first = repo.graph.get(tip_commit.parents[0])
        assert first.message == "add greeting"
        files = repo.files_at(result.new_tip)
        assert files["a.py"] == b"hello world\n"
        assert files["conf.ini"] == b"x=1\ny=2\n"

    def test_fixup_notes_call_the_message_noise(self):
        repo, base, tip = build()
        result = execute(
            repo, base, tip, plan(repo, base, tip)
        )
        notes = [entry.note for entry in result.entries]
        assert (
            "folded silently; fixup messages are noise "
            "by definition"
        ) in notes
