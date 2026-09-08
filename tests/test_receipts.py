from __future__ import annotations

from keel.filelocks import LockOffice
from keel.freeze import FreezeBoard
from keel.receipts import ReceiptsDesk


def busy_day() -> ReceiptsDesk:
    board = FreezeBoard()
    board.freeze("main", "the release cut", "priya")
    board.override("main", "dana", "priya", "HOT-9")
    board.lift("main", "priya")
    locks = LockOffice()
    locks.take("design.sketch", "priya", "rework")
    locks.steal(
        "design.sketch", "devi", "priya is on leave"
    )
    desk = ReceiptsDesk()
    desk.file_journal("freeze board", board.journal)
    desk.file_journal("lock office", locks.journal)
    desk.file_journal("mirror", [])
    return desk


class TestTheSpike:
    def test_journals_group_by_organ(self):
        page = busy_day().page()
        assert "freeze board (3 entr(ies)):" in page
        assert "lock office (2 entr(ies)):" in page
        assert (
            "5 entr(ies) from 2 organ(s), "
            "2 in capitals"
        ) in page

    def test_the_capitals_surface_first(self):
        page = busy_day().page()
        lock_section = page.split(
            "lock office (2 entr(ies)):"
        )[1]
        first_line = lock_section.strip().splitlines()[0]
        assert first_line.startswith("STOLEN:")

    def test_silence_is_filed_and_named(self):
        desk = busy_day()
        page = desk.page()
        assert (
            "1 organ(s) kept no journal: mirror"
        ) in page

    def test_the_empty_spike_says_so(self):
        assert ReceiptsDesk().page() == (
            "the spike is empty; no organ has reported"
        )

    def test_tomorrows_questions_are_flagged(self):
        page = busy_day().page()
        assert (
            "the capitals earned their capitals"
        ) in page
        assert "OVERRIDE: dana landed on main" in page
