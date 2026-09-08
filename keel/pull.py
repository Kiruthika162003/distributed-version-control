"""Pull: fetch plus a policy, with the policy's name on the receipt.

A pull is two decisions wearing one word, get their history
and reconcile it with ours, and the trouble starts when the
second decision is made silently by a default someone set
years ago. Here the policy is an argument with three
values and no default: ff_only advances our branch when
the fetch shows a fast-forward and refuses with the
divergence numbers when it does not, merge reconciles
divergence with a real merge commit through the standing
machinery, and ask does neither, reporting the situation
and stopping, the policy for people who want the numbers
before the verb. Every receipt names the policy that
produced it, because the pull that surprised somebody is
always the pull whose policy was invisible, and the fetch
happens exactly once regardless, since asking the remote
twice for one decision is how mirrors get rate limits.
"""

from __future__ import annotations

from keel.errors import Conflict, Invalid
from keel.merge import commit_merge, merge_commits
from keel.remotes import RemoteSet
from keel.repo import Repo

POLICIES = ("ff_only", "merge", "ask")


def pull(
    repo: Repo,
    remotes: RemoteSet,
    remote_name: str,
    branch: str,
    policy: str,
) -> str:
    if policy not in POLICIES:
        raise Invalid(
            f"{policy!r} is not a pull policy; choose "
            f"{', '.join(POLICIES)}, and there is no "
            "default because invisible policies are "
            "how pulls surprise people"
        )
    remotes.fetch(remote_name)
    remote = remotes.remotes[remote_name]
    their_tip = remote.observed.get(branch)
    if their_tip is None:
        raise Invalid(
            f"{remote_name} shows no branch {branch}"
        )
    our_tip = repo.refs.branches.get(branch)
    if our_tip is None:
        repo.refs.create_branch(branch, their_tip)
        return (
            f"[{policy}] {branch} adopted at "
            f"{their_tip[:8]}; we had no such branch"
        )
    if our_tip == their_tip:
        return (
            f"[{policy}] {branch} is current; the "
            "fetch was the whole errand"
        )
    ours = repo.graph.ancestors(our_tip)
    theirs = repo.graph.ancestors(their_tip)
    ahead = len(ours - theirs)
    behind = len(theirs - ours)
    if ahead == 0:
        repo.refs.move(
            branch,
            their_tip,
            reason=f"pull from {remote_name}",
        )
        return (
            f"[{policy}] {branch} fast-forwarded by "
            f"{behind} commit(s)"
        )
    if policy == "ff_only":
        raise Conflict(
            f"[ff_only] {branch} has diverged, ahead "
            f"{ahead} behind {behind}; this policy "
            "refuses to invent a merge, and the "
            "numbers are the start of the next "
            "decision"
        )
    if policy == "ask":
        return (
            f"[ask] {branch} has diverged, ahead "
            f"{ahead} behind {behind}; no verb was "
            "taken, the numbers came first as "
            "requested"
        )
    outcome = merge_commits(repo, our_tip, their_tip)
    if not outcome.is_clean():
        paths = ", ".join(sorted(outcome.conflicts))
        raise Conflict(
            f"[merge] the reconciliation conflicts on "
            f"{paths}; a person finishes what the "
            "policy started"
        )
    current = repo.refs.current_branch()
    if current != branch:
        repo.refs.checkout(branch)
    merged = commit_merge(
        repo,
        outcome,
        f"pull {branch} from {remote_name}",
    )
    if current != branch:
        repo.refs.checkout(current)
    return (
        f"[merge] {branch} reconciled as "
        f"{merged.address[:8]}, ahead {ahead} behind "
        f"{behind} resolved in one commit"
    )
