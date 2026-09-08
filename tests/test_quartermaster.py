from __future__ import annotations

from keel.budgets import BudgetBook
from keel.largefiles import make_pointer
from keel.quartermaster import storage_story
from keel.repo import Repo


def build(with_pointer: bool = False) -> Repo:
    repo = Repo.init()
    files = {
        "assets/big.bin": b"x" * 1500,
        "LICENSE": b"harbor v1\n",
        "vendor/LICENSE": b"harbor v1\n",
        "src/app.py": b"core\n",
    }
    if with_pointer:
        files["assets/huge.bin"] = make_pointer(
            b"y" * 50000
        )
    repo.commit(dict(files), "the hold is loaded")
    return repo


class TestTheStory:
    def test_the_four_strands_in_order(self):
        repo = build()
        budgets = BudgetBook()
        budgets.set_allowance("assets/", 2000)
        page = storage_story(repo, budgets=budgets)
        weight = page.index("weight:")
        waste = page.index("waste:")
        relief = page.index("relief:")
        plan = page.index("plan:")
        assert weight < waste < relief < plan
        assert "point assets/big.bin at the" in page
        assert "identical: LICENSE = vendor/LICENSE" in (
            page
        )

    def test_relief_counts_the_already_eaten(self):
        repo = build(with_pointer=True)
        page = storage_story(repo)
        assert (
            "1 path(s) already pointered to the "
            "warehouse (assets/huge.bin)"
        ) in page
        assert (
            "does not prescribe what is already eaten"
        ) in page

    def test_an_empty_warehouse_is_said(self):
        repo = build()
        page = storage_story(repo)
        assert "the warehouse stands empty" in page
        assert "a diet without a target is a mood" in (
            page
        )

    def test_the_story_ends_with_a_verb(self):
        repo = build()
        page = storage_story(repo)
        assert (
            "next action: assets/big.bin at 1500 "
            "byte(s)"
        ) in page
        assert "was a weather report" in page
