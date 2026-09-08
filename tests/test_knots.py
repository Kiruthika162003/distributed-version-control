from __future__ import annotations

from keel.knots import reading
from keel.repo import Repo

BASE = {"app.py": b"core\n"}


def linear(count: int) -> Repo:
    repo = Repo.init()
    text = b""
    for step in range(count):
        text += f"{step}\n".encode()
        repo.commit({"app.py": text}, f"step {step}")
    return repo


def with_merge() -> Repo:
    repo = linear(3)
    tip = repo.refs.current()
    side = repo.graph.create(
        tree=repo.graph.get(tip).tree,
        parents=(tip,),
        message="side",
    )
    merged = repo.commit_with_parents(
        {"app.py": b"merged\n"},
        "the meeting",
        (tip, side.address),
    )
    repo.refs.move("main", merged.address, reason="land")
    return repo


class TestTheReading:
    def test_becalmed_water_is_named(self):
        repo = linear(4)
        page = reading(repo, repo.refs.current())
        assert "becalmed" in page
        assert "saving its collisions up" in page

    def test_a_merge_registers_on_the_log(self):
        repo = with_merge()
        page = reading(
            repo, repo.refs.current(), window=10
        )
        assert page.startswith(
            "knots across 1 window(s) of 10: 1"
        )
        assert "tempo is a fact about the water" in (
            page
        )

    def test_the_verdict_is_never_a_grade(self):
        repo = linear(4)
        page = reading(repo, repo.refs.current())
        assert "not a score for the crew" in page
