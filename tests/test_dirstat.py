from __future__ import annotations

import pytest

from keel.dirstat import measure, render
from keel.errors import Invalid
from keel.repo import Repo


def build() -> tuple[Repo, str, str]:
    repo = Repo.init()
    first = repo.commit(
        {
            "web/app.py": b"x" * 100,
            "web/ui/panel.py": b"x" * 50,
            "api/server.py": b"x" * 100,
            "README.md": b"x" * 20,
        },
        "base",
    )
    second = repo.commit(
        {
            "web/app.py": b"x" * 160,
            "web/ui/panel.py": b"x" * 50,
            "api/server.py": b"x" * 40,
            "README.md": b"x" * 40,
        },
        "the change",
    )
    return repo, first.address, second.address


class TestMeasurement:
    def test_deltas_roll_up_to_top_level(self):
        repo, old, new = build()
        weights = measure(repo, old, new)
        assert weights == {
            "web": 60,
            "api": 60,
            "(root)": 20,
        }

    def test_deletions_count_as_change(self):
        repo, old, new = build()
        weights = measure(repo, old, new)
        assert weights["api"] == 60

    def test_depth_two_splits_the_web(self):
        repo, _old, new = build()
        repo_files = repo.files_at(new)
        deeper = dict(repo_files)
        deeper["web/ui/panel.py"] = b"x" * 90
        third = repo.commit(deeper, "panel grows")
        weights = measure(
            repo, new, third.address, depth=2
        )
        assert weights == {"web/ui": 40}

    def test_a_zero_depth_is_not_a_map(self):
        repo, old, new = build()
        with pytest.raises(Invalid):
            measure(repo, old, new, depth=0)


class TestRendering:
    def test_percentages_sum_to_one_hundred(self):
        repo, old, new = build()
        page = render(repo, old, new)
        shares = [
            int(line.strip().split("%")[0])
            for line in page.splitlines()
            if "%" in line
        ]
        assert sum(shares) == 100

    def test_heaviest_first_and_the_reminder(self):
        repo, old, new = build()
        page = render(repo, old, new)
        lines = page.splitlines()
        assert "140 byte(s) of motion" in lines[0]
        assert lines[1].strip().endswith(
            "api (60 byte(s))"
        )
        assert "landed somewhere too" in page

    def test_identical_trees_say_so(self):
        repo, old, _new = build()
        assert render(repo, old, old) == (
            "no change landed anywhere; same trees"
        )
