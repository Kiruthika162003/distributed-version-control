"""Remotes: other people's repositories, tracked without being trusted.

A remote is a name for someone else's repository plus the
local record of where their branches stood last time anyone
looked, and keeping those two ideas apart is the whole
design: remote-tracking state is a cache of observations,
never a thing to edit, so it updates only through fetch and
the divergence report reads from it without a network in
sight. Divergence is the number pair everyone wants before
deciding anything: ahead counts what we have that they lack,
behind counts the reverse, and the four shapes those numbers
make, current, ahead, behind, diverged, each end in a
different verb. The report never says "up to date" from a
stale observation without saying when the observation was
made, in fetch counts rather than clock time, because "as of
your last fetch" is the honest tense for everything a remote
appears to say.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing
from keel.repo import Repo
from keel.transfer import negotiate, receive


@dataclass
class Remote:
    name: str
    repo: Repo
    observed: dict[str, str] = field(default_factory=dict)
    fetches: int = 0


@dataclass
class RemoteSet:
    local: Repo
    remotes: dict[str, Remote] = field(default_factory=dict)

    def add(self, name: str, repo: Repo) -> str:
        if name in self.remotes:
            raise Invalid(f"{name} is already a remote")
        if not name.strip() or "/" in name:
            raise Invalid(
                f"{name!r} is not a remote name; one word, "
                "no slashes"
            )
        self.remotes[name] = Remote(name=name, repo=repo)
        return f"remote {name} added"

    def fetch(self, name: str) -> str:
        remote = self._get(name)
        wants = list(remote.repo.refs.branches.values())
        if not wants:
            raise Invalid(
                f"{name} has no branches to observe"
            )
        haves = list(self.local.graph.commits)
        batch = negotiate(remote.repo, wants, haves)
        receive(self.local.store, batch)
        for address, (kind, _payload) in batch.objects.items():
            if kind == "commit":
                remote_commit = remote.repo.graph.get(address)
                self.local.graph.commits[address] = (
                    remote_commit
                )
        remote.observed = dict(remote.repo.refs.branches)
        remote.fetches += 1
        return (
            f"fetched {name}: {batch.size()} object(s), "
            f"{len(remote.observed)} branch(es) observed"
        )

    def _get(self, name: str) -> Remote:
        remote = self.remotes.get(name)
        if remote is None:
            raise Missing(f"{name} is not a remote")
        return remote

    def divergence(
        self, branch: str, remote_name: str
    ) -> str:
        remote = self._get(remote_name)
        local_tip = self.local.refs.branches.get(branch)
        their_tip = remote.observed.get(branch)
        if local_tip is None:
            raise Missing(f"{branch} is not a local branch")
        if their_tip is None:
            return (
                f"{branch}: never observed on {remote_name}; "
                "fetch first, then ask again"
            )
        if remote.fetches == 0:
            raise Invalid(
                "divergence from zero observations is fiction"
            )
        ours = self.local.graph.ancestors(local_tip)
        theirs = self.local.graph.ancestors(their_tip)
        ahead = len(ours - theirs)
        behind = len(theirs - ours)
        tense = (
            f"as of fetch #{remote.fetches}"
        )
        if ahead == 0 and behind == 0:
            return f"{branch}: current with {remote_name} {tense}"
        if behind == 0:
            return (
                f"{branch}: ahead {ahead} {tense}; the verb "
                "is push"
            )
        if ahead == 0:
            return (
                f"{branch}: behind {behind} {tense}; the "
                "verb is merge or rebase"
            )
        return (
            f"{branch}: diverged, ahead {ahead} behind "
            f"{behind} {tense}; the verb is a conversation"
        )
