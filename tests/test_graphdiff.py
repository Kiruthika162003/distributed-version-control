from __future__ import annotations

from keel.graphdiff import compare, report
from keel.push import PushGate
from keel.remotes import RemoteSet
from keel.repo import Repo


def synced_pair() -> tuple[Repo, Repo]:
    ours = Repo.init()
    ours.commit({"a.py": b"1\n"}, "one")
    ours.commit({"a.py": b"1\n2\n"}, "two")
    shared = Repo.init()
    PushGate(remote=shared).push(ours, "main")
    theirs = Repo.init()
    lookout = RemoteSet(local=theirs)
    lookout.add("origin", shared)
    lookout.fetch("origin")
    return ours, theirs


class TestComparison:
    def test_identical_graphs_say_so(self):
        ours, theirs = synced_pair()
        page = report(ours, theirs)
        assert (
            "2 commit(s) shared, 0 only here, "
            "0 only there"
        ) in page
        assert "for once they are" in page

    def test_one_way_divergence_names_its_verb(self):
        ours, theirs = synced_pair()
        ours.commit({"a.py": b"1\n2\n3\n"}, "three")
        page = report(ours, theirs)
        assert "1 only here" in page
        assert "only here:" in page
        assert "three" in page
        assert "a push settles it" in page
        flipped = report(theirs, ours)
        assert "a fetch settles it" in flipped

    def test_both_ways_is_the_mirrors_conversation(
        self,
    ):
        ours, theirs = synced_pair()
        ours.commit({"a.py": b"1\n2\nours\n"}, "ours")
        theirs.refs.create_branch(
            "main",
            max(
                theirs.graph.commits.values(),
                key=lambda held: held.sequence,
            ).address,
        )
        theirs.refs.checkout("main")
        theirs.commit(
            {"a.py": b"1\n2\ntheirs\n"}, "theirs"
        )
        sides = compare(ours, theirs)
        assert len(sides["only_here"]) == 1
        assert len(sides["only_there"]) == 1
        page = report(ours, theirs)
        assert "diverged both ways" in page
        assert "who overwrote whom" in page
