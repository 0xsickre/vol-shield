"""Compute and publish vol_signal."""
from __future__ import annotations

import argparse
import json
import os
import sys

from vol_shield.data.repositories.shield_repository import insert_shield_snapshot, upsert_shield_signal
from vol_shield.services.build_shield_signal import build_shield_signal, public_vol_signal


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build vol_signal from live shield + hard gate")
    p.add_argument("--persist", action="store_true", help="Upsert shield_signal table")
    p.add_argument("--out", metavar="FILE", help="Write JSON snapshot")
    args = p.parse_args(argv)

    try:
        row = build_shield_signal()
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1

    public = public_vol_signal(row)
    out_doc = {**public, "shield": row.get("shield"), "gate": row.get("gate")}
    print(json.dumps(public, indent=2, default=str))

    if args.persist:
        upsert_shield_signal(row)
        insert_shield_snapshot(out_doc, as_of=public.get("as_of"))
        print(f"Persisted shield_signal as_of={public['as_of']}")

    out_path = args.out
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out_doc, f, indent=2, default=str)
        print(f"Wrote {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
