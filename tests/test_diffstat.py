from __future__ import annotations

from keel.diffstat import render_stat, stat_changes

OLD = {
    "app.py": b"one\ntwo\nthree",
    "logo.png": b"\x89PNG\x00old",
    "same.txt": b"unchanged",
}
NEW = {
    "app.py": b"one\nTWO\nthree\nfour",
    "logo.png": b"\x89PNG\x00newer bytes",
    "same.txt": b"unchanged",
}


class TestStats:
    def test_unchanged_files_stay_off_the_stat(self):
        stats = stat_changes(OLD, NEW)
        assert [s.path for s in stats] == [
            "app.py", "logo.png",
        ]

    def test_text_counts_lines_and_binary_counts_bytes(self):
        stats = {s.path: s for s in stat_changes(OLD, NEW)}
        assert stats["app.py"].added == 2
        assert stats["app.py"].removed == 1
        assert stats["logo.png"].binary
        assert stats["logo.png"].added == 8


class TestRendering:
    def test_bars_scale_to_the_largest_change(self):
        old = {"big.py": b"\n".join([b"x"] * 20), "small.py": b"a"}
        new = {
            "big.py": b"\n".join([b"y"] * 20),
            "small.py": b"b",
        }
        page = render_stat(stat_changes(old, new))
        big_line = next(
            line
            for line in page.splitlines()
            if line.startswith("big.py")
        )
        small_line = next(
            line
            for line in page.splitlines()
            if line.startswith("small.py")
        )
        assert big_line.count("+") + big_line.count("-") > (
            small_line.count("+") + small_line.count("-")
        )

    def test_binaries_are_stated_not_line_counted(self):
        page = render_stat(stat_changes(OLD, NEW))
        assert "binary (+8 -0 bytes)" in page

    def test_the_total_appears_exactly_once(self):
        page = render_stat(stat_changes(OLD, NEW))
        assert page.count("file(s) changed") == 1
        assert page.splitlines()[-1] == (
            "2 file(s) changed, 2 insertion(s), "
            "1 deletion(s), 1 binary"
        )

    def test_the_stat_of_nothing_is_nothing(self):
        assert render_stat([]) == (
            "no changes; the stat of nothing is nothing"
        )
