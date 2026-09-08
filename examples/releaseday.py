"""A release day: tag it, describe it, write the log, seal it, ship it.

The release is a set of claims and each tool notarizes one:
the tag holds the address still, describe names where any
later commit stands relative to it, the changelog sorts the
work with breaking changes never buried, the archive seals a
manifest, and the bundle carries history to machines with no
network in sight. Run with: python -m examples.releaseday
"""

from __future__ import annotations

from keel.archive import export, release_checksum
from keel.bundle import create_bundle, unbundle
from keel.changelog import render_changelog
from keel.describe import describe_head
from keel.repo import Repo
from keel.tags import TagStore


def main() -> int:
    repo = Repo.init()
    first = repo.commit(
        {"app.py": b"core\n", "README": b"a tool\n"},
        "feat: the core takes shape",
    )
    repo.commit(
        {"app.py": b"core\nfaster\n", "README": b"a tool\n"},
        "fix: skip the crash in the second pass",
    )
    repo.commit(
        {
            "app.py": b"core\nfaster\nrenamed api\n",
            "README": b"a tool\n",
        },
        "breaking: rename the entry points",
    )
    tip = repo.commit(
        {
            "app.py": b"core\nfaster\nrenamed api\n",
            "README": b"a tool, documented\n",
        },
        "docs: document the rename",
    )

    tags = TagStore(graph=repo.graph)
    tags.place(
        "v1.0", first.address, "the first sealed cut"
    )
    changes = render_changelog(
        repo, first.address, tip.address, "v1.1"
    )
    print(
        f"log:     {len(changes.splitlines())} changelog "
        "line(s) drafted for v1.1"
    )
    lines = changes.splitlines()
    heading = lines.index(
        "## Breaking changes, never buried"
    )
    print(f"break:   {lines[heading + 1]}")

    print(f"where:   {describe_head(repo, tags)}")
    tags.place("v1.1", tip.address, "the release cut")
    print(f"tag:     {tags.describe(tip.address)}")

    sealed = export(repo, tip.address, prefix="tool-1.1/")
    manifest = sealed.manifest()
    print(
        f"seal:    {len(manifest.splitlines())} manifest "
        f"line(s), checksum "
        f"{release_checksum(repo, tip.address)[:12]}"
    )
    print(f"verify:  {sealed.verify_against(manifest)}")

    bundle, sealed_manifest = create_bundle(repo, ["main"])
    print(f"bundle:  {bundle.listing()}")
    airgapped = Repo.init()
    print(
        "carry:   "
        + unbundle(airgapped, bundle, sealed_manifest)
    )
    airgapped.refs.create_branch(
        "main", bundle.tips["main"]
    )
    print(
        f"proof:   the far machine holds main at "
        f"{airgapped.refs.branches['main'][:8]}, same "
        f"address, no network involved"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
