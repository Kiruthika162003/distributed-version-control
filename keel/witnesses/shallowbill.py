"""The shallow clone billed against the decade it declined to download.

Ten commits of one growing file cost thirty objects at full
freight, ten commits and ten trees and ten blobs, nothing
shared because every edit mints new bytes. The witness
clones at depth three and reads the meter: nine objects, a
seventy percent saving, with exactly one boundary scar
recorded where the oldest shipped commit names a parent that
stayed home. The first deepen buys four more commits for
twelve more objects, the meter climbing linearly because the
corpus shares nothing, and the last deepen overshoots on
purpose, asking for ten when three remain, to prove the
fence caps at the root instead of inventing history to
sell. The bill ends balanced: thirty objects local, zero
scars, and the fence report switching from beyond the fence
to inside the shallow world for the same address that once
marked the edge.
"""

from __future__ import annotations

from keel.repo import Repo
from keel.shallow import ShallowClone
from keel.witnesses.finding import Testimony


def _decade() -> Repo:
    repo = Repo.init()
    text = b""
    for year in range(10):
        text += f"year {year}\n".encode()
        repo.commit({"annals.txt": text}, f"year {year}")
    return repo


def run() -> Testimony:
    source = _decade()
    full_cost = len(source.store.objects)
    clone = ShallowClone(source=source)
    clone.clone(depth=3)
    shipped_shallow = len(clone.local.store.objects)
    scar = next(iter(clone.boundary))
    scar_outside = "beyond the fence" in clone.fence_report(
        scar
    )

    clone.deepen(4)
    shipped_deepened = len(clone.local.store.objects)
    clone.deepen(10)
    shipped_final = len(clone.local.store.objects)
    scar_inside = (
        "inside the shallow world"
        in clone.fence_report(scar)
    )

    numbers = {
        "full_cost": full_cost,
        "shipped_at_depth_3": shipped_shallow,
        "saved_at_depth_3": full_cost - shipped_shallow,
        "shipped_after_deepen_4": shipped_deepened,
        "shipped_after_overshoot": shipped_final,
        "scars_left": len(clone.boundary),
        "scar_crossed_the_fence": (
            scar_outside and scar_inside
        ),
    }
    holds = (
        numbers["full_cost"] == 30
        and numbers["shipped_at_depth_3"] == 9
        and numbers["saved_at_depth_3"] == 21
        and numbers["shipped_after_deepen_4"] == 21
        and numbers["shipped_after_overshoot"] == 30
        and numbers["scars_left"] == 0
        and numbers["scar_crossed_the_fence"]
    )
    return Testimony(
        witness="shallowbill",
        claim=(
            "depth three ships 9 of 30 objects with one "
            "scar recorded, deepening buys history at "
            "linear freight, the overshoot caps at the "
            "root instead of inventing history to sell, "
            "and the old scar ends up inside the shallow "
            "world"
        ),
        numbers=numbers,
        holds=holds,
    )
