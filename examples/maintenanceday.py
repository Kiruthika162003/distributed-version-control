"""A maintenance day: the physical, the pinned census, the trim, the bill.

A branch dies, the reflog pins its commits through the first
collection, and only an explicit trim lets the second
collection present its itemized bill. The physical brackets
the whole day, because deletion tools deserve an audit on
both sides. Run with: python -m examples.maintenanceday
"""

from __future__ import annotations

from keel.fsck import Physical
from keel.gc import Collector
from keel.maintenance import MaintenanceRun
from keel.repo import Repo


def main() -> int:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"one\n", "lib.py": b"tool\n"}, "begin"
    )
    repo.commit(
        {"app.py": b"one\ntwo\n", "lib.py": b"tool\n"},
        "grow",
    )
    repo.branch_from_head("experiment")
    repo.refs.checkout("experiment")
    repo.commit(
        {
            "app.py": b"one\ntwo\n",
            "lib.py": b"tool\n",
            "wild.py": b"idea\n",
        },
        "wild idea",
    )
    repo.refs.checkout("main")
    print(f"fsck:    {Physical(repo=repo).run()}")

    print(f"delete:  {repo.refs.delete('experiment')}")
    collector = Collector(repo=repo)
    print(f"census:  {collector.census()}")
    print(f"collect: {collector.collect()}")

    repo.commit(
        {
            "app.py": b"one\ntwo\n",
            "lib.py": b"tool\nsharper\n",
        },
        "sharpen the tool",
    )
    print(f"trim:    {collector.trim_reflog(keep_last=1)}")
    print(f"collect: {collector.collect()}")

    print(f"fsck:    {Physical(repo=repo).run()}")
    print(MaintenanceRun(repo=repo).run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
