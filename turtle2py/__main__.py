"""Entry point: python -m turtle2py  (reads the two file names from stdin)."""

import sys

from .fields import turtle


def main():
    inp = sys.stdin.readline().strip()
    outp = sys.stdin.readline().strip()
    turtle(inp, outp)


if __name__ == "__main__":
    main()
