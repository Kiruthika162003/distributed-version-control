from __future__ import annotations

import pytest

from keel.blame import blame
from keel.errors import Invalid
from keel.repo import Repo
from keel.splice import splice


def elder_line() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"saga.txt": b"ancient line\n"}, "the founding"
    )
    repo.commit(
        {"saga.txt": b"ancient line\nmiddle age\n"},
        "the middle era",
    )
    return repo


def younger_line(seam: dict[str, bytes]) -> Repo:
    repo = Repo.init()
    repo.commit(dict(seam), "resumed from archive")
    repo.commit(
        {
            "saga.txt": (
                b"ancient line\nmiddle age\n"
                b"modern era\n"
            )
        },
        "the modern era",
    )
    return repo


class TestTheSeam:
    def test_a_matching_seam_joins_one_line(self):
        elder = elder_line()
        younger = younger_line(elder.head_files())
        joined, report = splice(elder, younger)
        assert (
            "spliced 2 elder and 1 younger commit(s) "
            "into one line of 3"
        ) in report
        assert joined.history()[0].endswith(
            "the modern era"
        )
        assert joined.history()[-1].endswith(
            "the founding"
        )

    def test_blame_walks_across_the_seam(self):
        elder = elder_line()
        younger = younger_line(elder.head_files())
        joined, _report = splice(elder, younger)
        rows = blame(
            joined, joined.refs.current(), "saga.txt"
        )
        messages = [
            joined.graph.get(row.commit).message
            for row in rows
        ]
        assert messages[0] == "the founding"
        assert messages[1] == "the middle era"
        assert messages[2] == "the modern era"

    def test_a_gapped_seam_is_refused_with_the_paths(
        self,
    ):
        elder = elder_line()
        younger = younger_line(
            {"saga.txt": b"a different resume\n"}
        )
        with pytest.raises(Invalid) as caught:
            splice(elder, younger)
        message = str(caught.value)
        assert "the seam does not match: saga.txt" in (
            message
        )
        assert "invents history" in message

    def test_merges_have_no_minutes_here(self):
        elder = elder_line()
        tip = elder.refs.current()
        side = elder.graph.create(
            tree=elder.graph.get(tip).tree,
            parents=(tip,),
            message="side",
        )
        merged = elder.commit_with_parents(
            {"saga.txt": b"m\n"},
            "meeting",
            (tip, side.address),
        )
        elder.refs.move(
            "main", merged.address, reason="land"
        )
        younger = younger_line(
            {"saga.txt": b"m\n"}
        )
        with pytest.raises(Invalid) as caught:
            splice(elder, younger)
        assert "no minutes for meetings" in str(
            caught.value
        )
