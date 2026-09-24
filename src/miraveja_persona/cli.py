"""The `miraveja-persona` command line (contracts/cli.md)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .check import Unreadable, exit_code
from .findings import Finding, render_json, render_text

USAGE = 2


class Usage(Exception):
    pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="miraveja-persona", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="write a scaffold for a new definition")
    new.add_argument("--name", required=True)
    new.add_argument("--synthetic", action="store_true")
    new.add_argument("-o", "--output", type=Path)

    check = sub.add_parser("check", help="check definitions and author's notes")
    check.add_argument("paths", nargs="+", type=Path)
    check.add_argument("--tree", type=Path)
    check.add_argument("--format", choices=["text", "json"], default="text")

    decide = sub.add_parser("decide", help="record a decision on an uncertain finding")
    decide.add_argument("fingerprint")
    decide.add_argument(
        "--as", dest="decision", required=True, choices=["accepted", "not-an-issue"]
    )
    decide.add_argument("--by", required=True)
    decide.add_argument("--tree", type=Path)

    pasts = sub.add_parser("pasts", help="list every shared past in the vault")
    pasts.add_argument("root", type=Path)
    pasts.add_argument("--format", choices=["text", "json"], default="text")

    freeze = sub.add_parser("freeze", help="record a definition's birth in the ledger")
    freeze.add_argument("path", type=Path)
    freeze.add_argument("--tree", type=Path, required=True)

    guard = sub.add_parser("guard", help="block persona content in a public repository")
    guard.add_argument("paths", nargs="*", type=Path)
    return parser


def _print_findings(findings: list[Finding], fmt: str) -> None:
    if fmt == "json":
        print(render_json(findings))
    elif findings:
        print(render_text(findings))


def _new(args: argparse.Namespace) -> int:
    from .scaffold import scaffold

    if not 1 <= len(args.name) <= 80:
        raise Usage("--name must be 1 to 80 characters")
    text = scaffold(args.name, "synthetic" if args.synthetic else "resident")
    if args.output is None:
        print(text, end="")
        return 0
    if args.output.exists():
        raise Usage(f"{args.output} exists; refusing to overwrite")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


def _check(args: argparse.Namespace) -> int:
    from .vault import check_paths

    result = check_paths(args.paths, tree=args.tree)
    _print_findings(result.findings, args.format)
    for stale in result.stale:
        print(f"stale decision {stale}: it matches no current finding", file=sys.stderr)
    return exit_code(result.findings)


def _decide(args: argparse.Namespace) -> int:
    from .decisions import decide

    ok, message = decide(args.fingerprint, args.decision, args.by, tree=args.tree)
    print(message, file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


def _pasts(args: argparse.Namespace) -> int:
    from .pasts import list_pasts, render

    print(render(list_pasts(args.root), args.format))
    return 0


def _freeze(args: argparse.Namespace) -> int:
    from .vault import freeze

    ok, message = freeze(args.path, args.tree)
    print(message, file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


def _guard(args: argparse.Namespace) -> int:
    from .guard import guard

    blocked = guard(args.paths)
    for item in blocked:
        print(item.render())
    if blocked:
        print(
            f"{len(blocked)} blocked: persona content must stay in the private vault",
            file=sys.stderr,
        )
        return 1
    return 0


HANDLERS = {
    "new": _new,
    "check": _check,
    "decide": _decide,
    "pasts": _pasts,
    "freeze": _freeze,
    "guard": _guard,
}


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
    except SystemExit as exit_:
        return USAGE if exit_.code else 0
    try:
        return HANDLERS[args.command](args)
    except (Usage, Unreadable) as problem:
        print(f"miraveja-persona: {problem}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    sys.exit(main())
