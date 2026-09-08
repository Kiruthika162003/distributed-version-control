from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.merge import commit_merge, merge_commits
from keel.repo import Repo
from keel.revparse import RevParser
from keel.tags import TagStore

BASE = {"a.txt": b"one"}


def storied() -> tuple[RevParser, Repo, list[str]]:
    repo = Repo.init()
    line = [repo.commit(dict(BASE), "c0").address]
    for number in range(1, 4):
        line.append(
            repo.commit(
                dict(BASE, **{"a.txt": f"v{number}".encode()}),
                f"c{number}",
            ).address
        )
    tags = TagStore(graph=repo.graph)
    tags.place("v1.0", line[1], "first")
    return RevParser(repo=repo, tags=tags), repo, line


class TestBases:
    def test_head_branch_tag_and_prefix_all_resolve(self):
        parser, _repo, line = storied()
        assert parser.resolve("HEAD") == line[3]
        assert parser.resolve("main") == line[3]
        assert parser.resolve("v1.0") == line[1]
        assert parser.resolve(line[2][:10]) == line[2]

    def test_the_armed_trap_is_not_sprung(self):
        parser, repo, line = storied()
        repo.refs.create_branch("v1.0", line[0])
        with pytest.raises(Invalid) as caught:
            parser.resolve("v1.0")
        assert "does not spring traps" in str(caught.value)

    def test_the_ambiguous_prefix_is_counted(self):
        parser, repo, _ = storied()
        firsts = [a[0] for a in repo.graph.commits]
        shared = next(
            (c for c in firsts if firsts.count(c) > 1), None
        )
        if shared is not None:
            with pytest.raises(Invalid) as caught:
                parser.resolve(shared)
            assert "must name exactly one" in str(caught.value)
        with pytest.raises(Missing):
            parser.resolve("zzzz")


class TestSuffixes:
    def test_tilde_walks_first_parents(self):
        parser, _, line = storied()
        assert parser.resolve("HEAD~2") == line[1]
        assert parser.resolve("main~3") == line[0]

    def test_suffixes_compose_left_to_right(self):
        parser, _, line = storied()
        assert parser.resolve("HEAD~1~1") == line[1]

    def test_falling_off_the_world_is_named(self):
        parser, _, _ = storied()
        with pytest.raises(Missing) as caught:
            parser.resolve("HEAD~9")
        assert "fell off the world" in str(caught.value)

    def test_caret_numbers_the_parents_of_a_merge(self):
        parser, repo, _ = storied()
        repo.branch_from_head("side")
        repo.refs.checkout("side")
        side = repo.commit(
            dict(BASE, **{"b.txt": b"x", "a.txt": b"v3"}),
            "side work",
        ).address
        repo.refs.checkout("main")
        outcome = merge_commits(
            repo, repo.refs.branches["main"], side
        )
        merged = commit_merge(repo, outcome, "merge side")
        assert parser.resolve("HEAD^1") == merged.parents[0]
        assert parser.resolve("HEAD^2") == merged.parents[1]
        with pytest.raises(Missing) as caught:
            parser.resolve("main~1^2")
        assert "numbered parents" in str(caught.value)

    def test_unknown_suffixes_are_refused(self):
        parser, _, _ = storied()
        with pytest.raises(Invalid):
            parser.resolve("HEAD@2")
