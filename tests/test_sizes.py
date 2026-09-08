from __future__ import annotations

from keel.repo import Repo
from keel.sizes import heaviest_blobs, measure, report


def modest_repo() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"core\n", "notes.md": b"n\n"}, "begin"
    )
    repo.commit(
        {"app.py": b"core\nmore\n", "notes.md": b"n\n"},
        "grow",
    )
    return repo


def hoarding_repo() -> Repo:
    repo = Repo.init()
    text = b""
    for step in range(5):
        text += b"x" * 300 + b"\n"
        repo.commit({"data.bin": text}, f"append {step}")
    return repo


class TestTheCensus:
    def test_weights_split_by_kind(self):
        repo = modest_repo()
        census = measure(repo)
        assert census.counts["commit"] == 2
        assert census.counts["blob"] == 3
        assert census.total_bytes() > 0

    def test_blobs_answer_to_their_paths(self):
        repo = modest_repo()
        census = measure(repo)
        named = set()
        for names in census.blob_names.values():
            named.update(names)
        assert named == {"app.py", "notes.md"}

    def test_heaviest_blobs_come_named_and_sorted(self):
        repo = hoarding_repo()
        census = measure(repo)
        heavy = heaviest_blobs(repo, census, top=2)
        assert len(heavy) == 2
        assert heavy[0][1] >= heavy[1][1]
        assert heavy[0][2] == ("data.bin",)


class TestPrescriptions:
    def test_the_hoard_and_the_heavy_are_both_named(self):
        repo = hoarding_repo()
        page = report(repo)
        assert (
            "point data.bin at the warehouse" in page
        )
        assert "past the heavy line of 1000" in page
        assert "delta-pack data.bin; 5 versions" in page

    def test_a_modest_attic_gets_no_lecture(self):
        repo = modest_repo()
        page = report(repo)
        assert (
            "no prescriptions; the attic is just full "
            "of attic"
        ) in page

    def test_the_kind_lines_read_as_a_ledger(self):
        repo = modest_repo()
        page = report(repo)
        assert "blob: 3 object(s)" in page
        assert "commit: 2 object(s)" in page
        assert "tree: 2 object(s)" in page
