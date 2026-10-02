"""Source-run terminal adapter for read-only project inspection."""

import argparse
import json
from pathlib import Path
import sys

from .inventory import FORMAT, InventoryError, compare, inventory, load_baseline, view
from .cache import cache_snapshot
from .knowledge import FORMAT as KNOWLEDGE_FORMAT, inspect_knowledge
from .receipts import FORMAT as RECEIPT_FORMAT, verify_project_receipt


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InventoryError("invalid_arguments", message)


def main(argv=None) -> int:
    parser = Parser(description="Read-only Universal IR project inspection prototype")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    command = commands.add_parser("inventory", help="Capture structure and evidence without source writes")
    command.add_argument("root", type=Path)
    command.add_argument("--path", default=".", help="Included relative file or directory to expand")
    command.add_argument("--limit", type=int, default=20)
    command.add_argument("--offset", type=int, default=0)
    command.add_argument("--full", action="store_true", help="Export full manifest for inspection or comparison")
    command.add_argument("--baseline", type=Path, help="Previous full inventory; never replaces current extraction")
    command.add_argument("--cache-dir", type=Path, help="Optional local snapshot storage outside the selected project; source is still fully rescanned")
    knowledge = commands.add_parser("knowledge", help="Inspect existing knowledge, evidence, and revision conflicts")
    knowledge.add_argument("root", type=Path)
    knowledge.add_argument("--id", dest="selected_id", help="Expand a logical knowledge identity")
    knowledge.add_argument("--limit", type=int, default=20)
    knowledge.add_argument("--offset", type=int, default=0)
    knowledge.add_argument("--full", action="store_true", help="Include all inspected revisions and coverage gaps")
    receipt = commands.add_parser("verify-receipt", help="Verify a host receipt under an explicit pinned policy; does not accept knowledge")
    receipt.add_argument("root", type=Path)
    receipt.add_argument("record_id")
    receipt.add_argument("--receipt", type=Path, required=True, help="External signed receipt JSON")
    receipt.add_argument("--policy", type=Path, required=True, help="External host-owned trust policy JSON")
    receipt.add_argument("--policy-id", required=True, help="Policy digest pinned by the host, not model-controlled inputs")
    output_format = FORMAT
    try:
        args = parser.parse_args(argv)
        if args.command == "knowledge":
            output_format = KNOWLEDGE_FORMAT
        elif args.command == "verify-receipt":
            output_format = RECEIPT_FORMAT
        if args.command != "verify-receipt" and (not 1 <= args.limit <= 200 or args.offset < 0):
            raise InventoryError("invalid_arguments", "limit must be 1..200 and offset must be nonnegative.")
        if args.command == "verify-receipt":
            output = verify_project_receipt(args.root, args.record_id, args.receipt, args.policy, args.policy_id)
        elif args.command == "knowledge":
            output = inspect_knowledge(args.root, selected_id=args.selected_id, offset=args.offset,
                                       limit=args.limit, full=args.full)
        else:
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
        print(json.dumps({"format": output_format, "status": "error",
                          "error": {"code": error.code, "message": str(error)}}, ensure_ascii=True),
              file=sys.stderr)
        return 3 if error.code == "unstable_inputs" else 2


if __name__ == "__main__":
    raise SystemExit(main())
