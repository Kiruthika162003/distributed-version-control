from __future__ import annotations

from keel.clone import clone
from keel.repo import Repo

BASE = {"app.py": b"core\n"}


def build() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "one")
    repo.commit(
        dict(BASE, **{"app.py": b"core\ntwo\n"}), "two"
    )
    repo.branch_from_head("feature")
    repo.refs.checkout("feature")
    repo.commit(
        dict(BASE, **{"app.py": b"core\ntwo\nf\n"}),
        "feature work",
    )
    return repo


class TestTheHonestClone:
    def test_the_copy_proves_itself_identical(self):
        source = build()
        copy, receipt = clone(source)
        assert (
            "cloned 3 commit(s) and 2 branch(es)"
        ) in receipt
        assert "identical to the address" in receipt
        assert (
            copy.refs.branches == source.refs.branches
        )
        assert copy.refs.head == "feature"

    def test_the_copy_stands_alone(self):
        source = build()
        copy, _receipt = clone(source)
        source.commit(
            dict(
                BASE,
                **{"app.py": b"core\ntwo\nf\nmore\n"},
            ),
            "after the clone",
        )
        assert len(copy.graph.commits) == 3
        tip = copy.refs.branches["feature"]
        assert copy.files_at(tip)["app.py"] == (
            b"core\ntwo\nf\n"
        )

    def test_an_empty_source_clones_to_empty(self):
        source = Repo.init()
        copy, receipt = clone(source)
        assert (
            "cloned 0 commit(s) and 0 branch(es)"
        ) in receipt
        assert copy.graph.commits == {}
