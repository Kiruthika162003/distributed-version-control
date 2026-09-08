from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.grep import grep_at, grep_between, render_grep
from keel.repo import Repo


def storied() -> tuple[Repo, str, str]:
    repo = Repo.init()
    old = repo.commit(
        {
            "app.py": b"use_old_api()\nprint(1)",
            "logo.png": b"\x89PNG\x00binary",
        },
        "release",
    ).address
    new = repo.commit(
        {
            "app.py": b"use_new_api()\nprint(1)",
            "extra.py": b"also use_new_api()",
            "logo.png": b"\x89PNG\x00binary",
        },
        "migrated",
    ).address
    return repo, old, new


class TestGrepAt:
    def test_hits_carry_path_line_and_text(self):
        repo, old, _ = storied()
        hits, _ = grep_at(repo, old, "use_old_api")
        assert len(hits) == 1
        assert hits[0].render() == (
            "app.py:1: use_old_api()"
        )

    def test_binaries_are_skipped_and_counted(self):
        repo, old, _ = storied()
        page = render_grep(repo, old, "PNG")
        assert "1 binary file(s) skipped and counted" in page
        assert "help nobody" in page

    def test_the_absent_pattern_names_the_commit(self):
        repo, old, _ = storied()
        assert f"is not in {old[:8]}" in render_grep(
            repo, old, "use_new_api"
        )

    def test_the_empty_pattern_is_refused(self):
        repo, old, _ = storied()
        with pytest.raises(Invalid):
            grep_at(repo, old, "")


class TestGrepBetween:
    def test_the_buckets_split_by_commit(self):
        repo, old, new = storied()
        report = grep_between(repo, "api", old, new)
        assert "1 only in" in report
        assert "2 only in" in report
        assert "old only: app.py: use_old_api()" in report
        assert (
            "new only: extra.py: also use_new_api()" in report
        )

    def test_shared_hits_are_counted_once(self):
        repo, old, new = storied()
        report = grep_between(repo, "print", old, new)
        assert report.startswith("'print': 1 shared")
