"""Explicitly reconcile one interrupted evaluation provider call as consumed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.budget import BudgetLedger, BudgetReconciliationError


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget-ledger", type=Path, required=True)
    parser.add_argument("--call-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--kind", choices=("model", "embedding"), required=True)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--model-limit", type=int, default=270)
    parser.add_argument("--embedding-limit", type=int, default=110)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        ledger = BudgetLedger(
            args.budget_ledger,
            args.model_limit,
            args.embedding_limit,
            require_existing=True,
        )
        result = ledger.reconcile_ambiguous(
            call_id=args.call_id,
            run_id=args.run_id,
            kind=args.kind,
            operator=args.operator,
        )
    except (BudgetReconciliationError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
