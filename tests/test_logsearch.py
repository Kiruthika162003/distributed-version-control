from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.logsearch import parse_query, render, search
from keel.repo import Repo


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    repo.commit(
        {"src/app.py": b"core\n", "docs/guide.md": b"g\n"},
        "begin the core",
    )
    repo.commit(
        {
            "src/app.py": b"core\nserve\n",
            "docs/guide.md": b"g\n",
        },
        "wire the server",
    )
    repo.commit(
        {
            "src/app.py": b"core\nserve\n",
            "docs/guide.md": b"g\nserver notes\n",
        },
        "document the server",
    )
    side = repo.graph.create(
        tree=repo.graph.get(
            repo.refs.current()
        ).tree,
        parents=(repo.refs.current(),),
        message="side line",
    )
    merged = repo.commit_with_parents(
        {
            "src/app.py": b"core\nserve\nmerged\n",
            "docs/guide.md": b"g\nserver notes\n",
        },
        "merge the side line",
        (repo.refs.current(), side.address),
    )
    repo.refs.move(
        "main", merged.address, reason="land the merge"
    )
    return repo, merged.address


class TestGrammar:
    def test_bare_words_and_keys_parse_together(self):
        query = parse_query("server path:src/ limit:3")
        assert query.words == ["server"]
        assert query.path_prefixes == ["src/"]
        assert query.limit == 3

    def test_unknown_keys_get_the_grammar_back(self):
        with pytest.raises(Invalid) as caught:
            parse_query("author:avery")
        assert "not in the grammar" in str(caught.value)
        assert "merge:only or merge:none" in str(
            caught.value
        )

    def test_contradictory_merge_modes_are_refused(self):
        with pytest.raises(Invalid) as caught:
            parse_query("merge:only merge:none")
        assert "the empty set" in str(caught.value)

    def test_seq_ranges_parse_both_shapes(self):
        single = parse_query("seq:2")
        assert (single.seq_low, single.seq_high) == (2, 2)
        span = parse_query("seq:1-3")
        assert (span.seq_low, span.seq_high) == (1, 3)


class TestSearching:
    def test_words_match_messages_case_blind(self):
        repo, tip = build()
        found = search(repo, tip, "SERVER")
        messages = [c.message for c in found]
        assert "wire the server" in messages
        assert "document the server" in messages
        assert "begin the core" not in messages

    def test_paths_trust_the_tree_not_the_message(self):
        repo, tip = build()
        found = search(repo, tip, "server path:src/")
        messages = [c.message for c in found]
        assert messages == ["wire the server"]

    def test_merge_only_finds_the_braid(self):
        repo, tip = build()
        found = search(repo, tip, "merge:only")
        assert [c.message for c in found] == [
            "merge the side line"
        ]

    def test_seq_windows_cut_both_ends(self):
        repo, tip = build()
        found = search(repo, tip, "seq:1-2")
        assert [c.message for c in found] == [
            "document the server",
            "wire the server",
        ]

    def test_limit_caps_from_the_tip(self):
        repo, tip = build()
        found = search(repo, tip, "merge:none limit:2")
        assert len(found) == 2


class TestRendering:
    def test_matches_render_as_oneliners(self):
        repo, tip = build()
        page = render(repo, tip, "server path:src/")
        assert page.startswith("1 commit(s) match")
        assert "wire the server" in page

    def test_no_results_blames_history_not_the_query(
        self,
    ):
        repo, tip = build()
        page = render(repo, tip, "zeppelin")
        assert "the history just disagrees" in page
