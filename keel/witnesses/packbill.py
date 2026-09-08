"""The pack bill: twelve edits, and the chain cap buys speed with bytes.

Thirteen versions of one thirty-line file weigh 8384 bytes
raw; the pack stores them in 2824, a 5560-byte saving, and
the composition is the finding: four full objects and nine
deltas, not one and twelve, because the chain-depth cap of
three forces a fresh full copy every fourth version. That
rhythm is the speed-for-bytes trade made visible, every
capped chain is reconstruction work bounded at three links,
and the guess this drill corrects is the naive one that a
delta store keeps exactly one full object: it keeps one per
chain, and the chains are short on purpose, so the bill for
fast reads is prepaid in full copies at regular intervals.
"""

from __future__ import annotations

from keel.packfile import Pack
from keel.witnesses.finding import Testimony


def run() -> Testimony:
    base_text = (
        "def handler(request):\n"
        + "    step_%d(request)\n" * 30
    ) % tuple(range(30))
    pack = Pack()
    previous = pack.add(base_text.encode())
    total_raw = len(base_text)
    for round_number in range(12):
        edited = base_text.replace(
            "step_5", f"step_5_v{round_number}"
        )
        payload = edited.encode()
        total_raw += len(payload)
        previous = pack.add(
            payload, base_address=previous
        )
    numbers = {
        "versions": 13,
        "raw_bytes": total_raw,
        "stored_bytes": pack.stored_bytes(),
        "saved_bytes": pack.naive_bytes()
        - pack.stored_bytes(),
        "full_objects": len(pack.full),
        "deltas": len(pack.deltas),
        "rejected": pack.rejected_deltas,
    }
    holds = (
        numbers["raw_bytes"] == 8384
        and numbers["stored_bytes"] == 2824
        and numbers["saved_bytes"] == 5560
        and numbers["full_objects"] == 4
        and numbers["deltas"] == 9
        and numbers["rejected"] == 0
    )
    return Testimony(
        witness="packbill",
        claim=(
            "the pack keeps one full object per chain, not "
            "one overall: four fulls and nine deltas store "
            "8384 raw bytes in 2824, the fast-read bill "
            "prepaid in full copies every fourth version"
        ),
        numbers=numbers,
        holds=holds,
    )
