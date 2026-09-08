from __future__ import annotations

from keel.repo import Repo
from keel.soundings import chart


def commit_tree(files: dict[str, bytes]) -> Repo:
    repo = Repo.init()
    repo.commit(files, "the tree under survey")
    return repo


class TestTheChart:
    def test_the_histogram_and_the_deepest(self):
        repo = commit_tree(
            {
                "README": b"r\n",
                "src/app.py": b"a\n",
                "src/web/ui/panel.py": b"p\n",
            }
        )
        page = chart(repo, repo.refs.current())
        assert "depth 0: 1 path(s)" in page
        assert "depth 1: 1 path(s)" in page
        assert "depth 3: 1 path(s)" in page
        assert (
            "deepest: src/web/ui/panel.py; where tab "
            "completion goes to die"
        ) in page

    def test_the_flat_verdict_is_guarded(self):
        repo = commit_tree(
            {"a.py": b"a\n", "b.py": b"b\n"}
        )
        page = chart(repo, repo.refs.current())
        assert (
            "a junk drawer wearing minimalism"
        ) in page

    def test_the_deep_verdict_asks_about_the_tax(self):
        repo = commit_tree(
            {
                "a/b/c/one.py": b"1\n",
                "a/b/c/d/two.py": b"2\n",
            }
        )
        page = chart(repo, repo.refs.current())
        assert (
            "does the nesting earn its tax"
        ) in page

    def test_the_navigable_middle_is_left_alone(self):
        repo = commit_tree(
            {
                "src/app.py": b"a\n",
                "src/core/engine.py": b"e\n",
                "docs/guide.md": b"g\n",
                "tests/unit/all.py": b"t\n",
            }
        )
        page = chart(repo, repo.refs.current())
        assert "navigable, and left alone" in page


class TestCorridors:
    def test_the_singleton_chain_is_listed(self):
        repo = commit_tree(
            {
                "src/only/deep/thing.py": b"t\n",
                "src/other.py": b"o\n",
            }
        )
        page = chart(repo, repo.refs.current())
        assert (
            "corridor: src/only/; depth without "
            "shelter"
        ) in page

    def test_a_sheltering_directory_is_not_a_corridor(
        self,
    ):
        repo = commit_tree(
            {
                "src/app.py": b"a\n",
                "src/web/panel.py": b"p\n",
                "src/web/button.py": b"b\n",
            }
        )
        page = chart(repo, repo.refs.current())
        assert "corridor" not in page
