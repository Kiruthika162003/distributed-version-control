from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.repo import Repo
from keel.shallow import ShallowClone


def deep_source(count: int = 10) -> Repo:
    repo = Repo.init()
    for number in range(count):
        repo.commit(
            {"a.txt": f"v{number}".encode()}, f"c{number}"
        )
    return repo


class TestCloning:
    def test_the_recent_past_ships_now(self):
        shallow = ShallowClone(source=deep_source())
        verdict = shallow.clone(depth=3)
        assert "shallow clone of 3 commit(s)" in verdict
        assert "scar(s) recorded, not hidden" in verdict
        assert len(shallow.local.graph.commits) == 3
        assert shallow.local.head_files() == {
            "a.txt": b"v9"
        }

    def test_the_scar_is_explicit(self):
        shallow = ShallowClone(source=deep_source())
        shallow.clone(depth=3)
        assert len(shallow.boundary) == 1
        scar = next(iter(shallow.boundary))
        assert "beyond the fence" in shallow.fence_report(scar)
        inside = shallow.local.refs.current()
        assert "inside the shallow world" in (
            shallow.fence_report(inside)
        )

    def test_a_second_clone_is_a_deepen(self):
        shallow = ShallowClone(source=deep_source())
        shallow.clone(depth=2)
        with pytest.raises(Invalid) as caught:
            shallow.clone(depth=5)
        assert "a deepen, not a second clone" in str(
            caught.value
        )

    def test_zero_depth_clones_a_rumor(self):
        with pytest.raises(Invalid):
            ShallowClone(source=deep_source()).clone(depth=0)


class TestDeepening:
    def test_each_deepen_extends_the_boundary_downward(self):
        shallow = ShallowClone(source=deep_source())
        shallow.clone(depth=3)
        verdict = shallow.deepen(more=4)
        assert "deepened by 4 commit(s)" in verdict
        assert len(shallow.local.graph.commits) == 7
        assert "does not pay for the decade" in verdict

    def test_the_fence_stops_at_the_root(self):
        shallow = ShallowClone(source=deep_source(count=4))
        shallow.clone(depth=2)
        shallow.deepen(more=10)
        assert shallow.boundary == set()
        verdict = shallow.deepen(more=5)
        assert "there is no deeper" in verdict

    def test_deepening_before_cloning_is_refused(self):
        with pytest.raises(Invalid):
            ShallowClone(source=deep_source()).deepen(more=2)
