import os
import pprint
import sys

from . import GlobExpr


def main(args: list[str]):
    if len(args) != 1:
        print("Expected only one argument", file=sys.stderr)
        exit(1)

    glob = sys.argv[1]
    expr = GlobExpr.parse(glob)
    if os.getenv("DEBUG_GLOBGROUPS") == "GlobExpr.parse":
        pprint.pprint(expr)
        print()
        print()
    for expand in expr.expand():
        print(expand)


if __name__ == "__main__":
    main(sys.argv[1:])
