from __future__ import annotations

from keel.graphstats import measure, narrate
from keel.repo import Repo


def linear_repo() -> tuple[Repo, str]:
    repo = Repo.init()
    text = b""
    for step in range(5):
        text += f"line {step}\n".encode()
        repo.commit({"work.txt": text}, f"step {step}")
    return repo, repo.refs.current()


def braided_repo() -> tuple[Repo, str]:
    repo = Repo.init()
    a = repo.commit({"work.txt": b"a\n"}, "a")
    b = repo.commit({"work.txt": b"a\nb\n"}, "b")
    side_one = repo.graph.create(
        tree=repo.graph.get(a.address).tree,
        parents=(a.address,),
        message="side one",
    )
    merge_one = repo.commit_with_parents(
        {"work.txt": b"a\nb\ns1\n"},
        "merge one",
        (b.address, side_one.address),
    )
    side_two = repo.graph.create(
        tree=repo.graph.get(b.address).tree,
        parents=(b.address,),
        message="side two",
    )
    merge_two = repo.commit_with_parents(
        {"work.txt": b"a\nb\ns1\ns2\n"},
        "merge two",
        (merge_one.address, side_two.address),
    )
    return repo, merge_two.address


class TestShapes:
    def test_a_railway_measures_as_one_run(self):
        repo, tip = linear_repo()
        shape = measure(repo, tip)
        assert shape.commits == 5
        assert shape.merges == 0
        assert shape.roots == 1
        assert shape.branch_points == 0
        assert shape.longest_linear_run == 5

    def test_a_braid_counts_its_merges_and_forks(self):
        repo, tip = braided_repo()
        shape = measure(repo, tip)
        assert shape.commits == 6
        assert shape.merges == 2
        assert shape.branch_points == 2
        assert shape.merge_density() > 0.2

    def test_a_federation_counts_its_roots(self):
        repo = Repo.init()
        main_tip = repo.commit(
            {"a.txt": b"a\n"}, "main root"
        )
        stray = repo.graph.create(
            tree=repo.snapshot_tree({"b.txt": b"b\n"}),
            parents=(),
            message="second root",
        )
        union = repo.commit_with_parents(
            {"a.txt": b"a\n", "b.txt": b"b\n"},
            "adopt",
            (main_tip.address, stray.address),
        )
        shape = measure(repo, union.address)
        assert shape.roots == 2


class TestVerdicts:
    def test_the_railway_earns_its_compliments(self):
        repo, tip = linear_repo()
        page = narrate(repo, tip)
        assert "longest linear run 5" in page
        assert "a railway" in page
        assert "both compliments" in page

    def test_the_braid_is_named_a_river(self):
        repo, tip = braided_repo()
        page = narrate(repo, tip)
        assert "a braided river" in page

    def test_the_federation_digs_separately(self):
        repo = Repo.init()
        main_tip = repo.commit({"a.txt": b"a\n"}, "root")
        stray = repo.graph.create(
            tree=repo.snapshot_tree({"b.txt": b"b\n"}),
            parents=(),
            message="second root",
        )
        union = repo.commit_with_parents(
            {"a.txt": b"a\n", "b.txt": b"b\n"},
            "adopt",
            (main_tip.address, stray.address),
        )
        page = narrate(repo, union.address)
        assert "a federation of 2 unrelated" in page

    def test_the_modest_shape_is_not_shamed(self):
        repo = Repo.init()
        repo.commit({"a.txt": b"a\n"}, "one")
        repo.commit({"a.txt": b"a\nb\n"}, "two")
        repo.commit({"a.txt": b"a\nb\nc\n"}, "three")
        shape = measure(repo, repo.refs.current())
        assert shape.longest_linear_run == 3
        page = narrate(repo, repo.refs.current())
        assert "a railway" in page
