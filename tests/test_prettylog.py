from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.prettylog import (
    Decorator,
    body_of,
    format_commit,
    pretty_log,
    subject_of,
)
from keel.repo import Repo
from keel.tags import TagStore


def build() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"one\n"},
        "first light\n\nthe story starts here",
    )
    repo.commit({"app.py": b"one\ntwo\n"}, "grow")
    return repo


class TestPlaceholders:
    def test_the_oneline_shape(self):
        repo = build()
        page = pretty_log(repo)
        lines = page.splitlines()
        assert len(lines) == 2
        assert lines[0].endswith("(main) grow")
        assert lines[1].endswith("first light")

    def test_subject_and_body_split_at_the_headline(self):
        message = "headline\n\nthe story\ncontinues"
        assert subject_of(message) == "headline"
        assert body_of(message) == "the story\ncontinues"

    def test_full_and_short_addresses_and_parents(self):
        repo = build()
        tip = repo.graph.get(repo.refs.current())
        rendered = format_commit(tip, "%H|%h|%p|%n")
        full, short, parents, sequence = rendered.split("|")
        assert full == tip.address
        assert short == tip.address[:8]
        assert parents == tip.parents[0][:8]
        assert sequence == "1"

    def test_a_literal_percent_survives(self):
        repo = build()
        tip = repo.graph.get(repo.refs.current())
        assert format_commit(tip, "100%%") == "100%"

    def test_unknown_placeholders_are_refused(self):
        repo = build()
        tip = repo.graph.get(repo.refs.current())
        with pytest.raises(Invalid) as caught:
            format_commit(tip, "%h %z")
        assert "%z at position 3" in str(caught.value)

    def test_a_template_ending_mid_placeholder_is_refused(
        self,
    ):
        repo = build()
        tip = repo.graph.get(repo.refs.current())
        with pytest.raises(Invalid):
            format_commit(tip, "%h %")


class TestDecorations:
    def test_branches_and_tags_decorate_their_commit(self):
        repo = build()
        tags = TagStore(graph=repo.graph)
        tags.place(
            "v1.0", repo.refs.current(), "first release"
        )
        repo.branch_from_head("release")
        page = pretty_log(repo, tags=tags)
        assert "(main, release, tag: v1.0) grow" in page

    def test_undecorated_commits_carry_no_parentheses(self):
        repo = build()
        decorator = Decorator(repo=repo)
        first = repo.graph.log(repo.refs.current())[-1]
        assert decorator.render(first.address) == ""


class TestLimits:
    def test_the_limit_trims_from_the_tip(self):
        repo = build()
        page = pretty_log(repo, limit=1)
        assert page.splitlines() == [
            page.splitlines()[0]
        ]
        assert "grow" in page
        assert "first light" not in page

    def test_a_zero_limit_is_refused(self):
        repo = build()
        with pytest.raises(Invalid) as caught:
            pretty_log(repo, limit=0)
        assert "silence wearing a formatter" in str(
            caught.value
        )
