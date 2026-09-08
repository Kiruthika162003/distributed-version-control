"""The command line: three verbs, one honest summary."""

from __future__ import annotations

import argparse
import sys


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
    arguments = parser.parse_args(argv)
    if arguments.command == "witnesses":
        from keel.witnesses import registry

        print(registry.report())
        return 0
    if arguments.command == "check":
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
    if arguments.command == "summary":
        from keel.witnesses import registry

        testimonies = registry.all_testimonies()
        failing = sum(
            1 for held in testimonies if not held.holds
        )
        print(
            f"{len(testimonies)} witnesses ({failing} broken)"
        )
        return 1 if failing else 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
