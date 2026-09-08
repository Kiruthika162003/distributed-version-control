from __future__ import annotations

from keel.drydock import yard_list
from keel.objects import BLOB
from keel.repo import Repo

DRIFTER = (
    b"line 1\nline 2\nline 3\nline 4\nline 5\n"
    b"line 6\nline 7\nline 8\nline 9\nline 10\n"
)
DRIFTED = (
    b"line 1\nline 2\nline 3\nline 4\nline 5\n"
    b"line 6\nline 7\nline 8\nline 9\nline TEN\n"
)


def seaworthy() -> Repo:
    repo = Repo.init()
    repo.commit({"src/app.py": b"core\n"}, "clean")
    return repo


def troubled() -> Repo:
    repo = Repo.init()
    first = repo.commit(
        {
            "src/App.py": b"a\n",
            "src/app.py": b"b\n",
            "util/helpers.py": DRIFTER,
            "scripts/helpers.py": DRIFTED,
        },
        "trouble base",
    )
    second = repo.commit(
        {
            "src/App.py": b"a\na2\n",
            "src/app.py": b"b\n",
            "util/helpers.py": DRIFTER,
            "scripts/helpers.py": DRIFTED,
        },
        "second",
    )
    merged = repo.commit_with_parents(
        repo.files_at(second.address),
        "pointless meeting",
        (second.address, first.address),
    )
    repo.refs.move(
        "main", merged.address, reason="land it"
    )
    blob = repo.store.put(BLOB, b"a\n")
    repo.store.objects[blob] = (BLOB, b"tampered\n")
    return repo


class TestTheYard:
    def test_seaworthy_says_so(self):
        assert yard_list(seaworthy()) == (
            "seaworthy; no orders, and the dock "
            "stands ready"
        )

    def test_orders_sort_hull_first(self):
        repo = troubled()
        page = yard_list(repo)
        lines = page.splitlines()
        assert lines[0].startswith("the yard list,")
        severities = [
            line.strip().split("]")[0].lstrip("[")
            for line in lines[1:-1]
        ]
        assert severities == sorted(
            severities,
            key=["hull", "rigging", "paint"].index,
        )
        assert severities[0] == "hull"

    def test_every_order_names_its_tool(self):
        repo = troubled()
        page = yard_list(repo)
        assert "through the airlock" in page
        assert "restructure map" in page
        assert "pick a canonical copy" in page
        assert (
            "without saying with what is a wish"
        ) in page

    def test_the_case_collision_reaches_the_rigging(
        self,
    ):
        repo = troubled()
        page = yard_list(repo)
        assert "case collision" in page
        assert "[rigging]" in page
