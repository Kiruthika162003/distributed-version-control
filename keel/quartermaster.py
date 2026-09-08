"""The quartermaster: one storage story from four ledgers, told in order.

Storage questions arrive tangled, why is the repository
heavy, what can go on a diet, what is already pointered
away, and the quartermaster untangles them by asking the
four organs that each hold a strand: the size census for
where the bytes live and its named heavyweights, the twins
report for content paying rent twice, the pointer count for
what the warehouse already carries so the diet does not
prescribe what is already eaten, and the budget headroom
when a book is kept, because a diet without a target is a
mood. The story is told in that order on purpose, weight
then waste then relief then plan, the order a quartermaster
actually thinks in, and each section keeps its organ's
voice under the standing paraphrase rule. The closing line
is the sheet's one addition: the single next action with
the biggest byte payoff, named, since a storage report
that ends without a verb was a weather report.
"""

from __future__ import annotations

from keel.budgets import BudgetBook
from keel.largefiles import is_pointer
from keel.repo import Repo
from keel.sizes import heaviest_blobs, measure
from keel.sizes import report as sizes_report
from keel.twins import report as twins_report


def storage_story(
    repo: Repo,
    budgets: BudgetBook | None = None,
) -> str:
    tip = repo.refs.current()
    sections = ["the quartermaster's storage story:"]

    sections.append(
        "weight:\n  "
        + sizes_report(repo).replace("\n", "\n  ")
    )
    sections.append(
        "waste:\n  "
        + twins_report(repo, tip).replace("\n", "\n  ")
    )

    files = repo.files_at(tip)
    pointered = sorted(
        path
        for path, content in files.items()
        if is_pointer(content)
    )
    if pointered:
        sections.append(
            "relief: "
            + f"{len(pointered)} path(s) already "
            "pointered to the warehouse ("
            + ", ".join(pointered)
            + "); the diet does not prescribe what "
            "is already eaten"
        )
    else:
        sections.append(
            "relief: nothing pointered yet; the "
            "warehouse stands empty"
        )

    if budgets is not None:
        sections.append(
            "plan:\n  "
            + budgets.headroom(repo).replace(
                "\n", "\n  "
            )
        )
    else:
        sections.append(
            "plan: no budget book kept; a diet "
            "without a target is a mood"
        )

    census = measure(repo)
    heavy = heaviest_blobs(repo, census, top=1)
    if heavy:
        address, size, names = heavy[0]
        target = names[0]
        sections.append(
            f"next action: {target} at {size} "
            f"byte(s) ({address[:8]}) is the biggest "
            "single payoff; a storage report that "
            "ends without a verb was a weather report"
        )
    return "\n\n".join(sections)
