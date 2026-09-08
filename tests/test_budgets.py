from __future__ import annotations

import pytest

from keel.budgets import BudgetBook
from keel.errors import Conflict, Invalid
from keel.repo import Repo


def build() -> tuple[Repo, BudgetBook]:
    repo = Repo.init()
    repo.commit(
        {
            "assets/logo.bin": b"x" * 80,
            "src/app.py": b"core\n",
        },
        "base",
    )
    book = BudgetBook()
    book.set_allowance("assets/", 100)
    return repo, book


class TestAllowances:
    def test_a_ceiling_below_one_is_a_ban(self):
        with pytest.raises(Invalid) as caught:
            BudgetBook().set_allowance("assets/", 0)
        assert "ban wearing a ledger" in str(
            caught.value
        )

    def test_nesting_makes_both_books_wrong(self):
        _repo, book = build()
        with pytest.raises(Invalid) as caught:
            book.set_allowance("assets/icons/", 50)
        assert "both books wrong" in str(caught.value)

    def test_files_need_a_slash(self):
        with pytest.raises(Invalid):
            BudgetBook().set_allowance("assets", 100)


class TestLandings:
    def test_an_affordable_landing_is_honored(self):
        repo, book = build()
        proposed = {
            "assets/logo.bin": b"x" * 95,
            "src/app.py": b"core\n",
        }
        assert book.check_landing(repo, proposed) == (
            "all 1 allowance(s) honored"
        )

    def test_the_overdraft_shows_its_arithmetic(self):
        repo, book = build()
        proposed = {
            "assets/logo.bin": b"x" * 80,
            "assets/video.bin": b"x" * 60,
            "src/app.py": b"core\n",
        }
        with pytest.raises(Conflict) as caught:
            book.check_landing(repo, proposed)
        message = str(caught.value)
        assert (
            "assets/: 80 now, 140 after this change, "
            "ceiling 100; over by 40"
        ) in message
        assert "is a negotiation" in message

    def test_the_unbudgeted_remainder_is_free(self):
        repo, book = build()
        proposed = {
            "assets/logo.bin": b"x" * 80,
            "src/app.py": b"x" * 100000,
        }
        assert "honored" in book.check_landing(
            repo, proposed
        )


class TestHeadroom:
    def test_the_diet_is_planned_with_numbers(self):
        repo, book = build()
        page = book.headroom(repo)
        assert (
            "assets/: 80 of 100 byte(s) spent (80%), "
            "20 of room"
        ) in page
        assert "planned diet" in page

    def test_no_allowances_is_said_not_hidden(self):
        repo, _book = build()
        page = BudgetBook().headroom(repo)
        assert "free and unwatched" in page
