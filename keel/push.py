"""Push: fast-forward or explain yourself, and the lease beats the force.

Pushing moves someone else's branch pointer, which is the
most social operation in the system, and the default rule
keeps it safe: a push lands only when the remote tip is an
ancestor of what is being pushed, a fast-forward, because
anything else silently discards commits someone may be
standing on. The bare force flag exists and is honest about
what it does, but the lease is the tool this module argues
for: force-with-lease names the tip the pusher believes the
remote holds, and the push lands only if that belief is still
true, so the race where a colleague pushed in the gap between
your fetch and your force overwrites nothing, it bounces with
both tips named. The bounce message distinguishes stale
belief from missing history, because the fixes differ: one is
a fetch, the other is a conversation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid
from keel.repo import Repo
from keel.transfer import negotiate, receive


@dataclass
class PushGate:
    remote: Repo
    pushes: int = 0
    bounces: list[str] = field(default_factory=list)

    def _ship(self, local: Repo, tip: str) -> int:
        haves = list(self.remote.graph.commits)
        batch = negotiate(local, wants=[tip], haves=haves)
        receive(self.remote.store, batch)
        for address, (kind, _payload) in batch.objects.items():
            if kind == "commit":
                self.remote.graph.commits[address] = (
                    local.graph.get(address)
                )
        return batch.size()

    def push(
        self, local: Repo, branch: str, force: bool = False
    ) -> str:
        tip = local.refs.branches.get(branch)
        if tip is None:
            raise Invalid(f"{branch} is not a local branch")
        their_tip = self.remote.refs.branches.get(branch)
        if their_tip is None:
            shipped = self._ship(local, tip)
            self.remote.refs.create_branch(branch, tip)
            self.pushes += 1
            return (
                f"{branch} created on the remote, "
                f"{shipped} object(s) shipped"
            )
        if their_tip == tip:
            return f"{branch} is already current; shipped nothing"
        shipped = self._ship(local, tip)
        if self.remote.graph.is_ancestor(their_tip, tip):
            self.remote.refs.move(
                branch, tip, reason="fast-forward push"
            )
            self.pushes += 1
            return (
                f"{branch} fast-forwarded, {shipped} "
                "object(s) shipped"
            )
        if force:
            self.remote.refs.move(
                branch,
                tip,
                reason="forced push",
                force=True,
            )
            self.pushes += 1
            return (
                f"{branch} FORCED to {tip[:8]}; the old tip "
                f"{their_tip[:8]} survives only in the "
                "remote's reflog"
            )
        bounce = (
            f"{branch} bounced: the remote tip "
            f"{their_tip[:8]} is not an ancestor of "
            f"{tip[:8]}; a plain push never discards commits "
            "someone may be standing on"
        )
        self.bounces.append(bounce)
        raise Invalid(bounce)

    def push_with_lease(
        self, local: Repo, branch: str, believed_tip: str
    ) -> str:
        their_tip = self.remote.refs.branches.get(branch)
        if their_tip is None:
            raise Invalid(
                f"{branch} does not exist remotely; a lease "
                "on nothing is a plain create"
            )
        if their_tip != believed_tip:
            bounce = (
                f"lease broken: you believed {branch} stood "
                f"at {believed_tip[:8]} but it stands at "
                f"{their_tip[:8]}; someone pushed in your "
                "gap, and the fix is a fetch, not a bigger "
                "hammer"
            )
            self.bounces.append(bounce)
            raise Invalid(bounce)
        return self.push(local, branch, force=True)
