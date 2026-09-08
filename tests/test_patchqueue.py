from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid, Missing
from keel.patchqueue import PatchQueue
from keel.repo import Repo

BASE = {"app.py": b"core\n", "conf.ini": b"x=1\n"}


def dressed() -> tuple[Repo, PatchQueue]:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    queue = PatchQueue(repo=repo)
    queue.new_patch(
        "logging", {"app.py": b"core\nlog\n"}
    )
    queue.push_patch()
    queue.new_patch(
        "metrics",
        {
            "app.py": b"core\nlog\nmetrics\n",
            "metrics.py": b"counter\n",
        },
    )
    queue.push_patch()
    return repo, queue


class TestWearing:
    def test_layers_stack_in_series_order(self):
        _repo, queue = dressed()
        files = queue.view()
        assert files["app.py"] == b"core\nlog\nmetrics\n"
        assert files["metrics.py"] == b"counter\n"

    def test_the_report_tells_worn_from_waiting(self):
        _repo, queue = dressed()
        queue.pop_patch()
        page = queue.series_report()
        assert "logging: worn, 1 path(s)" in page
        assert "metrics: waiting, 2 path(s)" in page

    def test_popping_restores_the_ground_exactly(self):
        _repo, queue = dressed()
        queue.pop_patch()
        files = queue.view()
        assert files["app.py"] == b"core\nlog\n"
        assert "metrics.py" not in files

    def test_moved_ground_refuses_the_push_by_path(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        queue = PatchQueue(repo=repo)
        queue.new_patch(
            "risky", {"conf.ini": b"x=1\ny=2\n"}
        )
        repo.commit(
            dict(BASE, **{"conf.ini": b"x=2\n"}),
            "head races ahead",
        )
        with pytest.raises(Conflict) as caught:
            queue.push_patch()
        message = str(caught.value)
        assert "risky expected different ground" in message
        assert "conf.ini" in message

    def test_the_stack_edges_are_refusals(self):
        _repo, queue = dressed()
        with pytest.raises(Missing):
            queue.push_patch()
        queue.pop_patch()
        queue.pop_patch()
        with pytest.raises(Missing):
            queue.pop_patch()


class TestBookkeeping:
    def test_duplicate_names_are_refused(self):
        _repo, queue = dressed()
        with pytest.raises(Invalid) as caught:
            queue.new_patch(
                "logging", {"app.py": b"other\n"}
            )
        assert "swap in the dark" in str(caught.value)

    def test_an_empty_patch_is_a_mood(self):
        _repo, queue = dressed()
        with pytest.raises(Invalid):
            queue.new_patch("mood", {})

    def test_refresh_edits_the_garment_only(self):
        _repo, queue = dressed()
        queue.refresh(
            {"metrics.py": b"counter\ngauge\n"}
        )
        assert queue.view()["metrics.py"] == (
            b"counter\ngauge\n"
        )
        with pytest.raises(Invalid) as caught:
            queue.refresh({"conf.ini": b"x=9\n"})
        assert "the garment, not the wardrobe" in str(
            caught.value
        )


class TestFolding:
    def test_the_bottom_folds_into_a_real_commit(self):
        repo, queue = dressed()
        receipt = queue.fold_bottom()
        assert receipt.startswith(
            "logging folded into history"
        )
        assert repo.history()[0].endswith("patch: logging")
        assert len(queue.series) == 1
        files = queue.view()
        assert files["app.py"] == b"core\nlog\nmetrics\n"

    def test_drift_is_caught_at_the_moment_of_permanence(
        self,
    ):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        queue = PatchQueue(repo=repo)
        queue.new_patch(
            "risky", {"conf.ini": b"x=1\ny=2\n"}
        )
        queue.push_patch()
        repo.commit(
            dict(BASE, **{"conf.ini": b"x=2\n"}),
            "head races ahead",
        )
        with pytest.raises(Conflict) as caught:
            queue.fold_bottom()
        assert "wrong moment to discover drift" in str(
            caught.value
        )

    def test_folding_bare_shoulders_is_refused(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        queue = PatchQueue(repo=repo)
        with pytest.raises(Missing):
            queue.fold_bottom()
