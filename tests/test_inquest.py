from __future__ import annotations

from keel.inquest import inquest
from keel.repo import Repo


def poisoned_history() -> tuple[Repo, str, str]:
    repo = Repo.init()
    good = repo.commit(
        {"app.py": b"core\n", "flag.txt": b"fine\n"},
        "all was well",
    )
    repo.commit(
        {
            "app.py": b"core\nmore\n",
            "flag.txt": b"fine\n",
        },
        "innocent growth",
    )
    repo.commit(
        {
            "app.py": b"core\nmore\n",
            "flag.txt": b"broken\n",
        },
        "the poisoning",
    )
    bad = repo.commit(
        {
            "app.py": b"core\nmore\nlater\n",
            "flag.txt": b"broken\n",
        },
        "life goes on",
    )
    return repo, good.address, bad.address


def oracle_for(repo: Repo):
    def oracle(address: str) -> int:
        files = repo.files_at(address)
        return (
            1
            if b"broken" in files.get("flag.txt", b"")
            else 0
        )

    return oracle


class TestTheProceeding:
    def test_the_verdict_names_commit_and_cost(self):
        repo, good, bad = poisoned_history()
        page = inquest(repo, good, bad, oracle_for(repo))
        assert "verdict:" in page
        assert "'the poisoning'" in page
        assert "oracle call(s)" in page

    def test_the_scene_is_examined_by_blame(self):
        repo, good, bad = poisoned_history()
        page = inquest(repo, good, bad, oracle_for(repo))
        assert "the change: 1 path(s): flag.txt" in page
        assert (
            "flag.txt: 1 line(s) at the tip still "
            "written by the culprit"
        ) in page
        assert "moved house" not in page

    def test_a_rewritten_scene_warns_about_theater(self):
        repo, good, _bad = poisoned_history()
        newest = repo.commit(
            {
                "app.py": b"core\nmore\nlater\n",
                "flag.txt": b"broken v2\n",
            },
            "someone repainted the scene",
        )
        page = inquest(
            repo, good, newest.address, oracle_for(repo)
        )
        assert "'the poisoning'" in page
        assert (
            "0 line(s) at the tip still written"
        ) in page
        assert "the bug may have moved house" in page
        assert "theater" in page

    def test_the_options_end_the_page(self):
        repo, good, bad = poisoned_history()
        page = inquest(repo, good, bad, oracle_for(repo))
        assert page.splitlines()[-1].startswith(
            "options: revert the culprit or fix forward"
        )
