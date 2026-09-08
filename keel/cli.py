"""The command line: a few verbs, every one of them accountable.

The verbs stay small because the library is the product and
the CLI is its lobby. What the lobby refuses to do is
summarize dishonestly: check exits nonzero the moment any
witness breaks, witness prints the numbers behind one claim
rather than a checkmark, and demo runs a full example
scenario end to end so the skeptic can watch the organs work
together instead of taking the test suite's word for it.
Unknown names are answered with the full roster, because a
tool that says unknown command without saying what it does
know is a locked door with no directory.
"""

from __future__ import annotations

import argparse
import importlib
import sys

from keel.voyages import names as example_names


def _witness_names() -> list[str]:
    from keel.witnesses import registry

    return [
        dotted.rsplit(".", 1)[-1]
        for dotted in registry.WITNESSES
    ]


def _run_witnesses() -> int:
    from keel.witnesses import registry

    print(registry.report())
    return 0


def _run_check() -> int:
    from keel.witnesses import registry

    failing = registry.broken()
    if failing:
        print(
            f"{len(failing)} witness(es) broken: "
            + ", ".join(failing)
        )
        return 1
    print("all witnesses hold")
    return 0


def _run_summary() -> int:
    from keel.witnesses import registry

    testimonies = registry.all_testimonies()
    failing = sum(
        1 for held in testimonies if not held.holds
    )
    print(
        f"{len(testimonies)} witnesses ({failing} broken)"
    )
    return 1 if failing else 0


def _run_witness(name: str) -> int:
    names = _witness_names()
    if name not in names:
        print(
            f"{name} is not a witness; the roster: "
            + ", ".join(names)
        )
        return 2
    module = importlib.import_module(
        f"keel.witnesses.{name}"
    )
    testimony = module.run()
    verdict = "holds" if testimony.holds else "BROKEN"
    print(f"{testimony.witness}: {verdict}")
    print(f"claim: {testimony.claim}")
    for key in sorted(testimony.numbers):
        print(f"  {key} = {testimony.numbers[key]}")
    return 0 if testimony.holds else 1


def _run_demo(name: str) -> int:
    known = example_names()
    if name not in known:
        print(
            f"{name} is not a demo; the roster: "
            + ", ".join(known)
        )
        return 2
    module = importlib.import_module(f"examples.{name}")
    return module.main()


def _run_numbers() -> int:
    from keel.witnesses import registry

    for testimony in registry.all_testimonies():
        print(f"{testimony.witness}:")
        for key in sorted(testimony.numbers):
            print(f"  {key} = {testimony.numbers[key]}")
    return 0


def _run_organs() -> int:
    from keel.organs import page

    print(page())
    return 0


def _run_voyages() -> int:
    from keel.voyages import page

    print(page())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="keel")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser(
        "witnesses", help="every testimony, one page"
    )
    commands.add_parser(
        "check", help="exit nonzero if any witness is broken"
    )
    commands.add_parser(
        "summary", help="one line: N witnesses (M broken)"
    )
    witness_parser = commands.add_parser(
        "witness", help="one testimony with its numbers"
    )
    witness_parser.add_argument("name")
    demo_parser = commands.add_parser(
        "demo", help="run one example scenario end to end"
    )
    demo_parser.add_argument("name")
    commands.add_parser(
        "numbers", help="every witness's measurements"
    )
    commands.add_parser(
        "organs",
        help="every module and its opening sentence",
    )
    commands.add_parser(
        "voyages",
        help="every example and its opening sentence",
    )
    arguments = parser.parse_args(argv)
    if arguments.command == "witnesses":
        return _run_witnesses()
    if arguments.command == "check":
        return _run_check()
    if arguments.command == "summary":
        return _run_summary()
    if arguments.command == "witness":
        return _run_witness(arguments.name)
    if arguments.command == "demo":
        return _run_demo(arguments.name)
    if arguments.command == "numbers":
        return _run_numbers()
    if arguments.command == "organs":
        return _run_organs()
    if arguments.command == "voyages":
        return _run_voyages()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
