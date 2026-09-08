from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.lostfound import claim, listing, shelf
from keel.repo import Repo


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    repo.commit({"app.py": b"one\n"}, "kept one")
    keeper = repo.commit(
        {"app.py": b"one\ntwo\n"}, "kept two"
    )
    repo.commit(
        {"app.py": b"one\ntwo\nthree\n"}, "lost three"
    )
    lost_two = repo.commit(
        {"app.py": b"one\ntwo\nthree\nfour\n"},
        "lost four",
    )
    repo.refs.move(
        "main",
        keeper.address,
        reason="reset away the pair",
        force=True,
    )
    repo.refs.reflog.clear()
    return repo, lost_two.address


class TestTheShelf:
    def test_orphans_are_shelved_newest_first(self):
        repo, newest = build()
        items = shelf(repo)
        assert [item.subject for item in items] == [
            "lost four",
            "lost three",
        ]
        assert items[0].address == newest
        assert items[0].file_count == 1

    def test_the_empty_shelf_is_good_news(self):
        repo = Repo.init()
        repo.commit({"app.py": b"one\n"}, "all kept")
        assert "the good news it sounds like" in (
            listing(repo)
        )

    def test_the_listing_invites_the_claim(self):
        repo, _newest = build()
        page = listing(repo)
        assert page.startswith(
            "2 unreachable commit(s), newest first:"
        )
        assert "'lost four'" in page
        assert "finding was only half the job" in page


class TestClaims:
    def test_a_claim_recovers_the_whole_chain(self):
        repo, newest = build()
        receipt = claim(repo, newest, "recovered")
        assert receipt.startswith(
            "recovered claims"
        )
        assert "4 commit(s) of history come back" in (
            receipt
        )
        assert repo.refs.branches["recovered"] == newest
        assert shelf(repo) == []

    def test_the_never_lost_cannot_be_claimed(self):
        repo, _newest = build()
        kept = repo.refs.branches["main"]
        with pytest.raises(Missing) as caught:
            claim(repo, kept, "recovered")
        assert "never lost or someone claimed" in str(
            caught.value
        )

    def test_claims_never_overwrite_the_living(self):
        repo, newest = build()
        with pytest.raises(Invalid) as caught:
            claim(repo, newest, "main")
        assert "never overwrite the living" in str(
            caught.value
        )
