from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.mergequeue import MergeQueue
from keel.repo import Repo

BASE = {
    "app.py": b"core\n",
    "docs.md": b"start\n",
    "lib.py": b"lib\n",
}


def build() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("alpha")
    repo.refs.checkout("alpha")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nalpha\n"}),
        "alpha touches app",
    )
    repo.refs.checkout("main")
    repo.branch_from_head("beta")
    repo.refs.checkout("beta")
    repo.commit(
        dict(BASE, **{"docs.md": b"start\nbeta\n"}),
        "beta touches docs",
    )
    repo.refs.checkout("main")
    repo.branch_from_head("clash")
    repo.refs.checkout("clash")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nclash\n"}),
        "clash touches app too",
    )
    repo.refs.checkout("main")
    repo.branch_from_head("gated")
    repo.refs.checkout("gated")
    repo.commit(
        dict(BASE, **{"lib.py": b"lib\nforbidden\n"}),
        "gated touches lib",
    )
    repo.refs.checkout("main")
    return repo


def smell_gate(files: dict[str, bytes]) -> str | None:
    if b"forbidden" in files.get("lib.py", b""):
        return "lib.py smells forbidden"
    return None


class TestSubmission:
    def test_the_receipt_promises_the_right_test(self):
        repo = build()
        queue = MergeQueue(repo=repo)
        receipt = queue.submit("alpha", "asha")
        assert receipt.startswith("alpha queued at #1")
        assert "at its turn, not as it stands now" in receipt

    def test_the_trunk_cannot_queue_onto_itself(self):
        repo = build()
        with pytest.raises(Invalid):
            MergeQueue(repo=repo).submit("main", "asha")

    def test_strangers_are_refused(self):
        repo = build()
        with pytest.raises(Missing):
            MergeQueue(repo=repo).submit("ghost", "asha")

    def test_double_queueing_is_refused(self):
        repo = build()
        queue = MergeQueue(repo=repo)
        queue.submit("alpha", "asha")
        with pytest.raises(Invalid) as caught:
            queue.submit("alpha", "asha")
        assert "lands once and confuses twice" in str(
            caught.value
        )


class TestProcessing:
    def test_the_batch_lands_and_bounces_in_order(self):
        repo = build()
        queue = MergeQueue(repo=repo)
        queue.submit("alpha", "asha")
        queue.submit("clash", "binh")
        queue.submit("beta", "chidi")
        queue.submit("gated", "devi")
        summary = queue.process(smell_gate)
        assert (
            "processed 4 entr(ies): 2 landed, 2 bounced"
        ) in summary
        states = {
            entry.branch: entry.state
            for entry in queue.entries
        }
        assert states == {
            "alpha": "landed",
            "clash": "bounced",
            "beta": "landed",
            "gated": "bounced",
        }

    def test_the_trunk_holds_the_combination_it_tested(
        self,
    ):
        repo = build()
        queue = MergeQueue(repo=repo)
        queue.submit("alpha", "asha")
        queue.submit("beta", "chidi")
        queue.process(smell_gate)
        files = repo.head_files()
        assert files["app.py"] == b"core\nalpha\n"
        assert files["docs.md"] == b"start\nbeta\n"
        assert files["lib.py"] == b"lib\n"

    def test_a_conflict_names_its_paths_and_blocks_nobody(
        self,
    ):
        repo = build()
        queue = MergeQueue(repo=repo)
        queue.submit("alpha", "asha")
        queue.submit("clash", "binh")
        queue.submit("beta", "chidi")
        queue.process(smell_gate)
        clash_entry = next(
            entry
            for entry in queue.entries
            if entry.branch == "clash"
        )
        assert (
            "conflicts with what landed ahead on app.py"
        ) in clash_entry.note
        beta_entry = next(
            entry
            for entry in queue.entries
            if entry.branch == "beta"
        )
        assert beta_entry.state == "landed"

    def test_the_gate_refusal_is_quoted_not_summarized(
        self,
    ):
        repo = build()
        queue = MergeQueue(repo=repo)
        queue.submit("gated", "devi")
        queue.process(smell_gate)
        entry = queue.entries[0]
        assert entry.note == (
            "gate said: lib.py smells forbidden"
        )

    def test_an_empty_queue_says_so(self):
        repo = build()
        queue = MergeQueue(repo=repo)
        assert "nothing to land" in queue.process(
            smell_gate
        )


class TestTheReport:
    def test_every_entry_keeps_its_position_and_state(
        self,
    ):
        repo = build()
        queue = MergeQueue(repo=repo)
        queue.submit("alpha", "asha")
        queue.submit("clash", "binh")
        queue.process(smell_gate)
        page = queue.report()
        assert "#1 alpha by asha: landed (as " in page
        assert (
            "#2 clash by binh: bounced (conflicts with "
            "what landed ahead on app.py)"
        ) in page
