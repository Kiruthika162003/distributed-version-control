from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid, Missing
from keel.rebaseplan import (
    execute,
    parse_plan,
    plan_range,
)
from keel.repo import Repo


def build() -> tuple[Repo, str, list[str]]:
    repo = Repo.init()
    base = repo.commit(
        {"a.txt": b"base\n", "b.txt": b"base\n"}, "ground"
    )
    one = repo.commit(
        {"a.txt": b"one\n", "b.txt": b"base\n"}, "touch a"
    )
    two = repo.commit(
        {"a.txt": b"one\n", "b.txt": b"two\n"}, "touch b"
    )
    three = repo.commit(
        {"a.txt": b"one\nmore\n", "b.txt": b"two\n"},
        "touch a again",
    )
    return (
        repo,
        base.address,
        [one.address, two.address, three.address],
    )


class TestParsing:
    def test_the_default_plan_picks_everything(self):
        repo, base, chain = build()
        text = plan_range(repo, base, chain[-1])
        lines = text.splitlines()
        assert len(lines) == 3
        assert lines[0] == f"pick {chain[0][:8]} touch a"

    def test_unknown_verbs_are_refused(self):
        with pytest.raises(Invalid) as caught:
            parse_plan("yeet abcd1234")
        assert "not a verb here" in str(caught.value)

    def test_reword_without_words_is_refused(self):
        with pytest.raises(Invalid) as caught:
            parse_plan("reword abcd1234")
        assert "pick with suspense" in str(caught.value)

    def test_an_empty_plan_is_refused(self):
        with pytest.raises(Invalid):
            parse_plan("# only a comment\n")


class TestExecution:
    def test_the_identity_plan_lands_everything(self):
        repo, base, chain = build()
        text = plan_range(repo, base, chain[-1])
        result = execute(repo, base, chain[-1], text)
        assert len(result.entries) == 3
        assert repo.files_at(result.new_tip) == (
            repo.files_at(chain[-1])
        )

    def test_a_clean_reorder_replays_change_by_change(
        self,
    ):
        repo, base, chain = build()
        text = "\n".join(
            [
                f"pick {chain[1][:8]}",
                f"pick {chain[0][:8]}",
                f"pick {chain[2][:8]}",
            ]
        )
        result = execute(repo, base, chain[-1], text)
        assert repo.files_at(result.new_tip) == (
            repo.files_at(chain[-1])
        )

    def test_a_dependent_reorder_raises_a_conflict(self):
        repo, base, chain = build()
        text = "\n".join(
            [
                f"pick {chain[2][:8]}",
                f"pick {chain[0][:8]}",
                f"pick {chain[1][:8]}",
            ]
        )
        with pytest.raises(Conflict) as caught:
            execute(repo, base, chain[-1], text)
        assert "merge without a base" in str(caught.value)

    def test_a_typed_drop_is_honored(self):
        repo, base, chain = build()
        text = "\n".join(
            [
                f"pick {chain[0][:8]}",
                f"drop {chain[1][:8]}",
                f"pick {chain[2][:8]}",
            ]
        )
        result = execute(repo, base, chain[-1], text)
        files = repo.files_at(result.new_tip)
        assert files["b.txt"] == b"base\n"
        assert files["a.txt"] == b"one\nmore\n"

    def test_a_vanished_commit_is_refused(self):
        repo, base, chain = build()
        text = "\n".join(
            [
                f"pick {chain[0][:8]}",
                f"pick {chain[2][:8]}",
            ]
        )
        with pytest.raises(Invalid) as caught:
            execute(repo, base, chain[-1], text)
        assert "type the drop" in str(caught.value)

    def test_squash_folds_files_and_both_messages(self):
        repo, base, chain = build()
        text = "\n".join(
            [
                f"pick {chain[0][:8]}",
                f"pick {chain[1][:8]}",
                f"squash {chain[2][:8]}",
            ]
        )
        result = execute(repo, base, chain[-1], text)
        landed = [
            entry
            for entry in result.entries
            if entry.new_address is not None
        ]
        tip = repo.graph.get(result.new_tip)
        assert tip.message == "touch b\n\ntouch a again"
        assert repo.files_at(result.new_tip)["a.txt"] == (
            b"one\nmore\n"
        )
        assert len({e.new_address for e in landed}) == 2

    def test_squash_cannot_lead(self):
        repo, base, chain = build()
        text = f"squash {chain[0][:8]}"
        with pytest.raises(Invalid) as caught:
            execute(repo, base, chain[0], text)
        assert "no predecessor" in str(caught.value)

    def test_reword_replaces_the_message(self):
        repo, base, chain = build()
        text = "\n".join(
            [
                f"reword {chain[0][:8]} better words",
                f"pick {chain[1][:8]}",
                f"pick {chain[2][:8]}",
            ]
        )
        result = execute(repo, base, chain[-1], text)
        first_landed = result.entries[0].new_address
        assert repo.graph.get(first_landed).message == (
            "better words"
        )

    def test_a_duplicate_pick_evaporates_with_a_note(self):
        repo, base, chain = build()
        text = "\n".join(
            [
                f"pick {chain[0][:8]}",
                f"pick {chain[0][:8]}",
                f"pick {chain[1][:8]}",
                f"pick {chain[2][:8]}",
            ]
        )
        result = execute(repo, base, chain[-1], text)
        notes = [entry.note for entry in result.entries]
        assert (
            "evaporated; every change was already in place"
            in notes
        )

    def test_a_stranger_in_the_plan_is_refused(self):
        repo, base, chain = build()
        text = "pick 00000000"
        with pytest.raises(Missing):
            execute(repo, base, chain[-1], text)

    def test_the_result_branch_lands_where_told(self):
        repo, base, chain = build()
        text = plan_range(repo, base, chain[-1])
        result = execute(
            repo, base, chain[-1], text, branch="replanned"
        )
        assert repo.refs.branches["replanned"] == (
            result.new_tip
        )
