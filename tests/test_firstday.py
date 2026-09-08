from __future__ import annotations

from keel.codeowners import OwnersFile
from keel.firstday import tour
from keel.repo import Repo
from keel.tags import TagStore


def build() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"src/app.py": b"core\n" * 30, "docs.md": b"d\n"},
        "begin the core",
    )
    repo.commit(
        {
            "src/app.py": b"core\n" * 35,
            "docs.md": b"d\n",
        },
        "grow the core",
    )
    repo.commit(
        {
            "src/app.py": b"core\n" * 40,
            "docs.md": b"d\n",
        },
        "grow it again",
    )
    return repo


class TestTheTour:
    def test_the_computed_tour_hits_every_stop(self):
        repo = build()
        tags = TagStore(graph=repo.graph)
        tags.place(
            "v1.0",
            repo.graph.log(repo.refs.current())[-1]
            .address,
            "first cut",
        )
        owners = OwnersFile.parse("src/ team-core\n")
        page = tour(
            repo, tags=tags, owners=owners
        )
        assert page.startswith("welcome; main stands at")
        assert "3 commit(s) behind it" in page
        assert "the era: v1.0+2" in page
        assert "the shape: 0 merge(s)" in page
        assert "src/app.py" in page
        assert "everyone else does" in page
        assert "src/ answers to team-core" in page

    def test_the_conversation_is_verbatim_and_recent(
        self,
    ):
        repo = build()
        page = tour(repo)
        lines = page.splitlines()
        start = lines.index(
            "the current conversation, last 3 "
            "subject(s):"
        )
        assert lines[start + 1] == "  grow it again"
        assert lines[start + 3] == "  begin the core"

    def test_absent_organs_are_named_with_fallbacks(
        self,
    ):
        repo = build()
        page = tour(repo)
        assert "no tags placed yet" in page
        assert (
            "ask whoever answers, and consider writing "
            "the file your first contribution"
        ) in page
