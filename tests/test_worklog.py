from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.repo import Repo
from keel.worklog import digest, render


def busy_then_quiet() -> tuple[Repo, str]:
    repo = Repo.init()
    app = b""
    for step in range(4):
        app += f"app {step}\n".encode()
        repo.commit(
            {"app.py": app, "docs.md": b"d\n"},
            f"app step {step}",
        )
    repo.commit(
        {"app.py": app, "docs.md": b"d\nmore\n"},
        "touch the docs once",
    )
    return repo, repo.refs.current()


class TestWindows:
    def test_buckets_split_on_sequence(self):
        repo, tip = busy_then_quiet()
        windows = digest(repo, tip, window=3)
        assert len(windows) == 2
        assert (windows[0].start, windows[0].end) == (
            0,
            2,
        )
        assert windows[0].commits == 3
        assert windows[1].commits == 2

    def test_the_busiest_path_is_the_sentence(self):
        repo, tip = busy_then_quiet()
        windows = digest(repo, tip, window=3)
        assert windows[0].busiest == "app.py"
        assert windows[0].busiest_touches == 3

    def test_a_zero_window_is_refused(self):
        repo, tip = busy_then_quiet()
        with pytest.raises(Invalid):
            digest(repo, tip, window=0)


class TestTheRendering:
    def test_the_page_reads_like_a_standup(self):
        repo, tip = busy_then_quiet()
        page = render(repo, tip, window=3)
        assert page.startswith("2 window(s) of 3:")
        assert "busiest app.py (3 touch(es))" in page

    def test_a_falling_pace_is_called_past_the_margin(
        self,
    ):
        repo, tip = busy_then_quiet()
        page = render(repo, tip, window=3)
        assert "the pace is falling: 2 against 3" in page

    def test_steady_is_respectable(self):
        repo = Repo.init()
        text = b""
        for step in range(4):
            text += f"{step}\n".encode()
            repo.commit({"a.txt": text}, f"step {step}")
        page = render(repo, repo.refs.current(), window=2)
        assert (
            "steady, which is a respectable thing to "
            "say about work"
        ) in page

    def test_one_window_is_a_snapshot(self):
        repo = Repo.init()
        repo.commit({"a.txt": b"a\n"}, "only")
        page = render(repo, repo.refs.current(), window=5)
        assert "a snapshot, not a trend" in page
