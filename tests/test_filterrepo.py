from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.filterrepo import (
    expunge,
    filter_history,
    keep_prefixes,
    strip_paths,
)
from keel.repo import Repo


def build_history() -> tuple[Repo, list[str]]:
    repo = Repo.init()
    first = repo.commit(
        {
            "src/app.py": b"one\n",
            "secrets.env": b"KEY=hunter2\n",
        },
        "begin",
    )
    second = repo.commit(
        {
            "src/app.py": b"one\ntwo\n",
            "secrets.env": b"KEY=hunter2\n",
            "docs/guide.md": b"read\n",
        },
        "grow",
    )
    third = repo.commit(
        {
            "src/app.py": b"one\ntwo\n",
            "secrets.env": b"KEY=rotated\n",
            "docs/guide.md": b"read\n",
        },
        "rotate key",
    )
    fourth = repo.commit(
        {
            "src/app.py": b"one\ntwo\nthree\n",
            "secrets.env": b"KEY=rotated\n",
            "docs/guide.md": b"read\n",
        },
        "more",
    )
    return repo, [
        first.address,
        second.address,
        third.address,
        fourth.address,
    ]


class TestFilterHistory:
    def test_kept_paths_survive_with_old_messages(self):
        repo, addresses = build_history()
        report = filter_history(
            repo,
            addresses[-1],
            keep_prefixes("src/"),
            branch="src-only",
        )
        tip_files = repo.files_at(report.new_tip)
        assert tip_files == {
            "src/app.py": b"one\ntwo\nthree\n"
        }
        rebuilt = repo.graph.get(report.new_tip)
        assert rebuilt.message == "more"

    def test_commits_with_no_surviving_changes_evaporate(
        self,
    ):
        repo, addresses = build_history()
        report = filter_history(
            repo, addresses[-1], keep_prefixes("src/")
        )
        assert report.dropped() == (addresses[2],)
        assert len(report.mapping()) == 3

    def test_every_new_address_differs_from_the_old(self):
        repo, addresses = build_history()
        report = filter_history(
            repo, addresses[-1], keep_prefixes("src/")
        )
        for old, new in report.mapping().items():
            assert old != new

    def test_the_result_branch_is_created(self):
        repo, addresses = build_history()
        report = filter_history(
            repo,
            addresses[-1],
            keep_prefixes("src/"),
            branch="src-only",
        )
        assert (
            repo.refs.branches["src-only"]
            == report.new_tip
        )

    def test_a_filter_that_keeps_nothing_says_so(self):
        repo, addresses = build_history()
        report = filter_history(
            repo, addresses[-1], keep_prefixes("nope/")
        )
        assert report.new_tip is None
        assert len(report.dropped()) == 4
        assert "nothing survived" in report.narrate()

    def test_merges_are_refused(self):
        repo, addresses = build_history()
        side = repo.graph.create(
            tree=repo.graph.get(addresses[0]).tree,
            parents=(addresses[0],),
            message="side",
        )
        merged = repo.commit_with_parents(
            {"src/app.py": b"merged\n"},
            "merge",
            (addresses[-1], side.address),
        )
        with pytest.raises(Invalid) as caught:
            filter_history(
                repo, merged.address, keep_prefixes("src/")
            )
        assert "straight line" in str(caught.value)

    def test_the_narration_maps_old_to_new(self):
        repo, addresses = build_history()
        report = filter_history(
            repo, addresses[-1], keep_prefixes("src/")
        )
        page = report.narrate()
        assert "3 commit(s) rewritten, 1 evaporated" in page
        assert addresses[2][:8] in page
        assert "no longer exists" in page


class TestExpunge:
    def test_the_secret_is_gone_from_every_commit(self):
        repo, addresses = build_history()
        result = expunge(
            repo,
            addresses[-1],
            "secrets.env",
            branch="cleaned",
        )
        for new_address in result.report.mapping().values():
            assert "secrets.env" not in repo.files_at(
                new_address
            )

    def test_the_rotation_commit_evaporates(self):
        repo, addresses = build_history()
        result = expunge(
            repo, addresses[-1], "secrets.env"
        )
        assert result.appearances == 4
        assert result.report.dropped() == (addresses[2],)

    def test_the_narration_says_rotate_first(self):
        repo, addresses = build_history()
        result = expunge(
            repo, addresses[-1], "secrets.env"
        )
        page = result.narrate()
        assert "appeared in 4 of 4 commit(s)" in page
        assert "rotate the secret" in page

    def test_expunging_a_stranger_is_refused(self):
        repo, addresses = build_history()
        with pytest.raises(Missing) as caught:
            expunge(repo, addresses[-1], "ghost.txt")
        assert "a story about a rewrite" in str(
            caught.value
        )


class TestPredicates:
    def test_prefixes_match_directories_and_exact_paths(
        self,
    ):
        keep = keep_prefixes("src/", "README.md")
        assert keep("src/deep/file.py")
        assert keep("README.md")
        assert not keep("srcery.py")
        assert not keep("docs/guide.md")

    def test_strip_removes_only_the_named_paths(self):
        keep = strip_paths("secrets.env")
        assert keep("src/app.py")
        assert not keep("secrets.env")
