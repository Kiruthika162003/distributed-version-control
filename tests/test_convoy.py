from __future__ import annotations

import pytest

from keel.convoy import land_convoy
from keel.errors import Conflict, Invalid
from keel.repo import Repo

BASE = {
    "api.py": b"api\n",
    "caller_one.py": b"c1\n",
    "caller_two.py": b"c2\n",
}


def build() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    for name, changes in (
        ("api-change", {"api.py": b"api v2\n"}),
        (
            "caller-one",
            {"caller_one.py": b"c1 on v2\n"},
        ),
        (
            "caller-two",
            {"caller_two.py": b"c2 on v2\n"},
        ),
    ):
        repo.branch_from_head(name)
        repo.refs.checkout(name)
        repo.commit(
            dict(BASE, **changes), f"{name} work"
        )
        repo.refs.checkout("main")
    return repo


def open_gate(_files: dict[str, bytes]) -> str | None:
    return None


class TestLandings:
    def test_the_convoy_lands_as_one_pointer_move(self):
        repo = build()
        receipt = land_convoy(
            repo,
            "main",
            ["api-change", "caller-one", "caller-two"],
            open_gate,
        )
        assert receipt.startswith("the convoy lands: 3")
        assert "today it was together" in receipt
        files = repo.head_files()
        assert files["api.py"] == b"api v2\n"
        assert files["caller_one.py"] == b"c1 on v2\n"
        assert files["caller_two.py"] == b"c2 on v2\n"

    def test_one_ship_is_not_a_convoy(self):
        repo = build()
        with pytest.raises(Invalid):
            land_convoy(
                repo, "main", ["api-change"], open_gate
            )


class TestScattering:
    def test_a_collision_lands_nothing(self):
        repo = build()
        repo.refs.checkout("caller-one")
        repo.commit(
            dict(
                BASE,
                **{
                    "api.py": b"api rogue\n",
                    "caller_one.py": b"c1 on v2\n",
                },
            ),
            "caller one goes rogue",
        )
        repo.refs.checkout("main")
        before = repo.refs.branches["main"]
        with pytest.raises(Conflict) as caught:
            land_convoy(
                repo,
                "main",
                ["api-change", "caller-one"],
                open_gate,
            )
        message = str(caught.value)
        assert (
            "the convoy scatters: caller-one collides "
            "on api.py"
        ) in message
        assert repo.refs.branches["main"] == before

    def test_the_gate_turns_away_the_combination(self):
        repo = build()
        before = repo.refs.branches["main"]

        def picky(files: dict[str, bytes]) -> str | None:
            if b"api v2" in files.get("api.py", b""):
                return "v2 is not certified yet"
            return None

        with pytest.raises(Conflict) as caught:
            land_convoy(
                repo,
                "main",
                ["api-change", "caller-one"],
                picky,
            )
        assert (
            "turned away at the final combination: "
            "v2 is not certified yet"
        ) in str(caught.value)
        assert repo.refs.branches["main"] == before
