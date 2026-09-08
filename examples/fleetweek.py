"""A fleet week: the accord, the wake, the convoy, and one clean decision.

Three branches sail from one accord, the frontier names who
is farthest out, the wake prices what a rewrite of the
accord would cost, the convoy lands the API change with
both its callers together or not at all, and the week
closes with a ref transaction retiring the landed branches
as one decision. Run with: python -m examples.fleetweek
"""

from __future__ import annotations

from keel.compass import orient
from keel.convoy import land_convoy
from keel.frontier import report as frontier_report
from keel.reftx import RefTransaction
from keel.repo import Repo
from keel.wake import report as wake_report

BASE = {
    "api.py": b"api\n",
    "caller_one.py": b"c1\n",
    "caller_two.py": b"c2\n",
}


def main() -> int:
    repo = Repo.init()
    repo.commit(dict(BASE), "founding")
    accord = repo.commit(
        dict(BASE, **{"api.py": b"api stable\n"}),
        "the accord",
    )
    for name, changes, extra in (
        ("api-change", {"api.py": b"api v2\n"}, 0),
        (
            "caller-one",
            {"caller_one.py": b"c1 on v2\n"},
            1,
        ),
        (
            "caller-two",
            {"caller_two.py": b"c2 on v2\n"},
            2,
        ),
    ):
        repo.refs.checkout("main")
        repo.branch_from_head(name)
        repo.refs.checkout(name)
        files = dict(BASE)
        files["api.py"] = b"api stable\n"
        files.update(changes)
        repo.commit(files, f"{name} work")
        for step in range(extra):
            key = next(iter(changes))
            files[key] = (
                files[key] + f"polish {step}\n".encode()
            )
            repo.commit(
                dict(files), f"{name} polish {step}"
            )
    repo.refs.checkout("main")

    page = frontier_report(
        repo,
        ["main", "api-change", "caller-one", "caller-two"],
    )
    print(page.splitlines()[0])
    print(page.splitlines()[-1])

    wake_page = wake_report(repo, accord.address)
    print(wake_page.splitlines()[0])
    print(wake_page.splitlines()[2])

    print(
        land_convoy(
            repo,
            "main",
            ["api-change", "caller-one", "caller-two"],
            lambda _files: None,
        )
    )

    transaction = RefTransaction(repo=repo)
    for name in (
        "api-change",
        "caller-one",
        "caller-two",
    ):
        transaction.stage(name, delete=True)
    print(transaction.apply().splitlines()[0])

    print(
        orient(
            repo, accord.address
        ).splitlines()[1]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
