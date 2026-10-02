"""Source-run terminal adapter for the local inventory proof."""

import argparse
import json
from pathlib import Path
import sys

from .inventory import FORMAT, InventoryError, compare, inventory, load_baseline, view
from .cache import cache_snapshot


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InventoryError("invalid_arguments", message)


def main(argv=None) -> int:
    parser = Parser(description="Read-only Universal IR project inventory prototype")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    command = commands.add_parser("inventory", help="Capture structure and evidence without source writes")
    command.add_argument("root", type=Path)
    command.add_argument("--path", default=".", help="Included relative file or directory to expand")
    command.add_argument("--limit", type=int, default=20)
    command.add_argument("--offset", type=int, default=0)
    command.add_argument("--full", action="store_true", help="Export full manifest for inspection or comparison")
    command.add_argument("--baseline", type=Path, help="Previous full inventory; never replaces current extraction")
    command.add_argument("--cache-dir", type=Path, help="Optional local snapshot storage outside the selected project; source is still fully rescanned")
    try:
        args = parser.parse_args(argv)
        if not 1 <= args.limit <= 200 or args.offset < 0:
            raise InventoryError("invalid_arguments", "limit must be 1..200 and offset must be nonnegative.")
        baseline = load_baseline(args.baseline) if args.baseline else None
        result = inventory(args.root)
        output = view(result, selection=args.path, offset=args.offset, limit=args.limit, full=args.full)
        if baseline:
            output["comparison"] = compare(baseline, result, limit=args.limit, full=args.full)
        if args.cache_dir is not None:
            cached = cache_snapshot(result, args.cache_dir)
            output["cache"] = cached["cache"]
            if args.full:
                output["manifest"] = cached["manifest"]
        print(json.dumps(output, ensure_ascii=True, indent=2, allow_nan=False))
        return 0
    except InventoryError as error:
        print(json.dumps({"format": FORMAT, "status": "error",
                          "error": {"code": error.code, "message": str(error)}}, ensure_ascii=True),
              file=sys.stderr)
        return 3 if error.code == "unstable_inputs" else 2


if __name__ == "__main__":
    raise SystemExit(main())
