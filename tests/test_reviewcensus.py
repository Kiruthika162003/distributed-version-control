from __future__ import annotations

from keel.repo import Repo
from keel.reviewcensus import census


def build(messages: list[str]) -> tuple[Repo, str]:
    repo = Repo.init()
    text = b""
    for message in messages:
        text += b"x\n"
        repo.commit({"app.py": text}, message)
    return repo, repo.refs.current()


class TestReviewers:
    def test_vouches_are_ranked(self):
        repo, tip = build(
            [
                "one\n\nReviewed-by: priya\n",
                (
                    "two\n\nReviewed-by: priya\n"
                    "Reviewed-by: devi\n"
                ),
                "three\n\nReviewed-by: priya\n",
            ]
        )
        page = census(repo, tip)
        assert page.startswith(
            "4 review vouch(es) from 2 reviewer(s):"
        )
        lines = page.splitlines()
        assert lines[1] == "  priya: 3"
        assert lines[2] == "  devi: 1"

    def test_concentration_is_said_while_both_remain(
        self,
    ):
        repo, tip = build(
            [
                "one\n\nReviewed-by: priya\n",
                "two\n\nReviewed-by: devi\n",
                "three\n\nReviewed-by: priya\n",
            ]
        )
        page = census(repo, tip)
        assert (
            "the top two carry 3 of 3; a bus factor "
            "wearing a compliment"
        ) in page


class TestKeys:
    def test_the_near_miss_counts_as_nothing(self):
        repo, tip = build(
            [
                "one\n\nReviewd-by: priya\n",
                "two\n\nReviewed-by: devi\n",
            ]
        )
        page = census(repo, tip)
        assert (
            "near-miss: 'reviewd-by' (1 use(s)) is "
            "one slip from 'reviewed-by'"
        ) in page
        assert (
            "looks like a trailer and counts as "
            "nothing"
        ) in page

    def test_clean_spelling_earns_trust(self):
        repo, tip = build(
            ["one\n\nReviewed-by: priya\n"]
        )
        page = census(repo, tip)
        assert (
            "every trailer key spells itself; the "
            "counts can be trusted"
        ) in page
