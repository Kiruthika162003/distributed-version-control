from __future__ import annotations

import pytest

from keel.blameignore import (
    blame_with_ignores,
    ignore_list_policy,
)
from keel.errors import Invalid, Missing
from keel.repo import Repo


def reformatted() -> tuple[Repo, str]:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"def real_work():\nreturn 1"},
        "the real author",
    )
    reformat = repo.commit(
        {"app.py": b"def real_work():\n    return 1"},
        "reformat everything",
    ).address
    return repo, reformat


class TestSeeingThrough:
    def test_the_button_presser_loses_the_credit(self):
        repo, reformat = reformatted()
        rows = blame_with_ignores(
            repo,
            repo.refs.current(),
            "app.py",
            ignored={reformat},
        )
        indented = next(
            row
            for row in rows
            if row.text.strip() == "return 1"
        )
        assert indented.credited != reformat
        assert reformat in indented.seen_through
        assert "seen through" in indented.render(repo)

    def test_without_the_list_the_reformat_claims_it(self):
        repo, reformat = reformatted()
        rows = blame_with_ignores(
            repo,
            repo.refs.current(),
            "app.py",
            ignored=set(),
        )
        indented = next(
            row
            for row in rows
            if row.text.strip() == "return 1"
        )
        assert indented.credited == reformat
        assert indented.seen_through == ()

    def test_ignored_revisions_must_exist(self):
        repo, _ = reformatted()
        with pytest.raises(Missing):
            blame_with_ignores(
                repo,
                repo.refs.current(),
                "app.py",
                ignored={"feedfacefeedfacefeed"},
            )


class TestThePolicy:
    def test_the_policy_refuses_to_guess(self):
        statement = ignore_list_policy(["abc123"])
        assert "nothing lands here automatically" in statement
        assert "corruption with a good excuse" in statement

    def test_the_empty_list_needs_no_statement(self):
        with pytest.raises(Invalid):
            ignore_list_policy([])
