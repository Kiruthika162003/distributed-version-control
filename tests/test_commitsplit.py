from __future__ import annotations

import pytest

from keel.commitsplit import SplitGroup, split
from keel.errors import Invalid, Missing
from keel.repo import Repo


def build() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"core\n", "docs.md": b"d\n"}, "base"
    )
    repo.commit(
        {
            "app.py": b"core\nserve\n",
            "docs.md": b"d\nserver docs\n",
            "tests.py": b"test_serve\n",
        },
        "the everything commit",
    )
    return repo


def good_groups() -> list[SplitGroup]:
    return [
        SplitGroup(
            message="wire the server",
            paths=("app.py",),
        ),
        SplitGroup(
            message="cover the server",
            paths=("tests.py",),
        ),
        SplitGroup(
            message="document the server",
            paths=("docs.md",),
        ),
    ]


class TestTheCut:
    def test_three_pieces_replace_the_boulder(self):
        repo = build()
        boulder = repo.refs.branches["main"]
        result = split(repo, "main", good_groups())
        assert len(result.landed) == 3
        assert repo.refs.branches["main"] == (
            result.new_tip
        )
        assert repo.files_at(result.new_tip) == (
            repo.files_at(boulder)
        )

    def test_each_piece_carries_only_its_paths(self):
        repo = build()
        result = split(repo, "main", good_groups())
        first_address = result.landed[0][1]
        files = repo.files_at(first_address)
        assert files["app.py"] == b"core\nserve\n"
        assert files["docs.md"] == b"d\n"
        assert "tests.py" not in files

    def test_the_boulder_survives_in_the_reflog(self):
        repo = build()
        boulder = repo.refs.branches["main"]
        split(repo, "main", good_groups())
        assert any(
            boulder[:8] in entry
            for entry in repo.refs.reflog
        )

    def test_the_narration_shows_the_proof(self):
        repo = build()
        result = split(repo, "main", good_groups())
        page = result.narrate()
        assert page.startswith("3 commit(s) replace")
        assert "wire the server" in page
        assert "byte for byte" in page


class TestTheAudit:
    def test_an_unclaimed_path_stops_everything(self):
        repo = build()
        groups = good_groups()[:2]
        with pytest.raises(Invalid) as caught:
            split(repo, "main", groups)
        message = str(caught.value)
        assert "unclaimed change(s): docs.md" in message
        assert "vanishes silently" in message

    def test_a_double_claim_is_twice_storied(self):
        repo = build()
        groups = good_groups()
        groups[2] = SplitGroup(
            message="document the server",
            paths=("docs.md", "app.py"),
        )
        with pytest.raises(Invalid) as caught:
            split(repo, "main", groups)
        assert "twice landed is twice storied" in str(
            caught.value
        )

    def test_a_stranger_path_is_refused(self):
        repo = build()
        groups = good_groups()
        groups[0] = SplitGroup(
            message="wire the server",
            paths=("app.py", "ghost.py"),
        )
        with pytest.raises(Missing) as caught:
            split(repo, "main", groups)
        assert "what changed, not what exists" in str(
            caught.value
        )

    def test_a_split_into_one_piece_is_a_rename(self):
        repo = build()
        with pytest.raises(Invalid) as caught:
            split(
                repo,
                "main",
                [
                    SplitGroup(
                        message="everything again",
                        paths=(
                            "app.py",
                            "docs.md",
                            "tests.py",
                        ),
                    )
                ],
            )
        assert "a rename of the problem" in str(
            caught.value
        )

    def test_a_merge_tip_is_refused(self):
        repo = build()
        tip = repo.refs.branches["main"]
        side = repo.graph.create(
            tree=repo.graph.get(tip).tree,
            parents=(tip,),
            message="side",
        )
        merged = repo.commit_with_parents(
            {"app.py": b"m\n"},
            "merge",
            (tip, side.address),
        )
        repo.refs.move(
            "main", merged.address, reason="land merge"
        )
        with pytest.raises(Invalid) as caught:
            split(repo, "main", good_groups())
        assert "one parent to measure" in str(
            caught.value
        )
