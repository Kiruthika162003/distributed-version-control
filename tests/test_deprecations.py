from __future__ import annotations

import pytest

from keel.deprecations import DeprecationLedger
from keel.errors import Invalid, Missing
from keel.repo import Repo

BASE = {
    "old_api.py": b"legacy\n",
    "new_api.py": b"shiny\n",
}


def build() -> tuple[Repo, DeprecationLedger]:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    return repo, DeprecationLedger(repo=repo)


class TestNotices:
    def test_a_notice_names_successor_and_deadline(self):
        _repo, ledger = build()
        receipt = ledger.declare(
            "old_api.py", "new_api.py", 10
        )
        assert receipt == (
            "old_api.py deprecated in favor of "
            "new_api.py, gone by sequence 10"
        )

    def test_ghosts_frighten_nobody(self):
        _repo, ledger = build()
        with pytest.raises(Missing):
            ledger.declare("ghost.py", "new_api.py", 10)

    def test_no_forwarding_address_no_eviction(self):
        _repo, ledger = build()
        with pytest.raises(Invalid) as caught:
            ledger.declare("old_api.py", "  ", 10)
        assert "forwarding address" in str(caught.value)

    def test_a_past_deadline_is_an_apology(self):
        _repo, ledger = build()
        with pytest.raises(Invalid) as caught:
            ledger.declare(
                "old_api.py", "new_api.py", 0
            )
        assert "apology in advance" in str(caught.value)


class TestTheAudit:
    def test_touches_since_notice_are_counted_as_votes(
        self,
    ):
        repo, ledger = build()
        ledger.declare("old_api.py", "new_api.py", 10)
        repo.commit(
            dict(
                BASE,
                **{"old_api.py": b"legacy\npatched\n"},
            ),
            "someone touches the dying",
        )
        page = ledger.audit()
        assert "on schedule" in page
        assert "1 touch(es) since notice" in page
        assert (
            "a vote against the migration finishing"
        ) in page

    def test_overdue_gets_its_name_in_capitals(self):
        repo, ledger = build()
        ledger.declare("old_api.py", "new_api.py", 2)
        for step in range(3):
            repo.commit(
                dict(
                    BASE,
                    **{
                        "new_api.py": (
                            f"shiny\n{step}\n".encode()
                        )
                    },
                ),
                f"unrelated {step}",
            )
        page = ledger.audit()
        assert "old_api.py: OVERDUE" in page

    def test_a_gone_path_is_invited_to_retire(self):
        repo, ledger = build()
        ledger.declare("old_api.py", "new_api.py", 10)
        repo.commit(
            {"new_api.py": b"shiny\n"}, "the migration"
        )
        page = ledger.audit()
        assert (
            "old_api.py: gone; retire the notice"
        ) in page


class TestRetirement:
    def test_retiring_the_living_is_refused(self):
        _repo, ledger = build()
        ledger.declare("old_api.py", "new_api.py", 10)
        with pytest.raises(Invalid) as caught:
            ledger.retire("old_api.py")
        assert "how the file comes back" in str(
            caught.value
        )

    def test_the_dead_retire_with_credit(self):
        repo, ledger = build()
        ledger.declare("old_api.py", "new_api.py", 10)
        repo.commit(
            {"new_api.py": b"shiny\n"}, "the migration"
        )
        receipt = ledger.retire("old_api.py")
        assert receipt == (
            "old_api.py retired; new_api.py carries on"
        )
        assert (
            "nothing here is dying" in ledger.audit()
        )
