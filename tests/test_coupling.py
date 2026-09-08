from __future__ import annotations

import pytest

from keel.coupling import measure, report
from keel.errors import Invalid
from keel.repo import Repo


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    files = {
        "api/schema.py": b"v0\n",
        "web/client.py": b"v0\n",
        "docs/notes.md": b"n0\n",
    }
    repo.commit(dict(files), "found")
    files["api/schema.py"] = b"v1\n"
    files["web/client.py"] = b"v1\n"
    repo.commit(dict(files), "round one together")
    files["api/schema.py"] = b"v2\n"
    repo.commit(dict(files), "schema alone")
    files["api/schema.py"] = b"v3\n"
    files["web/client.py"] = b"v3\n"
    repo.commit(dict(files), "round two together")
    files["web/client.py"] = b"v4\n"
    repo.commit(dict(files), "client alone")
    files["docs/notes.md"] = b"n1\n"
    repo.commit(dict(files), "notes alone")
    return repo, repo.refs.current()


class TestMarriages:
    def test_the_couple_is_found_with_its_rate(self):
        repo, tip = build()
        marriages = measure(repo, tip)
        assert len(marriages) == 1
        held = marriages[0]
        assert held.left == "api/schema.py"
        assert held.right == "web/client.py"
        assert held.together == 3
        assert held.rate == 0.75

    def test_the_single_lives_are_left_alone(self):
        repo, tip = build()
        marriages = measure(repo, tip)
        partners = {m.left for m in marriages} | {
            m.right for m in marriages
        }
        assert "docs/notes.md" not in partners

    def test_the_floors_have_teeth(self):
        repo, tip = build()
        assert measure(repo, tip, count_floor=4) == []
        assert (
            measure(repo, tip, rate_floor=0.8) == []
        )

    def test_the_floor_refusals_use_the_exact_words(self):
        repo, tip = build()
        with pytest.raises(Invalid) as coincidence:
            measure(repo, tip, rate_floor=0.0)
        assert "coincidence" in str(coincidence.value)
        with pytest.raises(Invalid) as anecdote:
            measure(repo, tip, count_floor=1)
        assert "anecdotes" in str(anecdote.value)


class TestTheReport:
    def test_the_cross_house_marriage_is_called_out(self):
        repo, tip = build()
        page = report(repo, tip)
        assert (
            "api/schema.py + web/client.py: together "
            "3 time(s), 75% of the quieter one"
        ) in page
        assert (
            "the boundary is drawn where the work is "
            "not"
        ) in page

    def test_single_lives_read_as_such(self):
        repo = Repo.init()
        repo.commit({"a.py": b"a\n"}, "one")
        repo.commit({"a.py": b"a\nb\n"}, "two")
        page = report(repo, repo.refs.current())
        assert "the files live single lives" in page
