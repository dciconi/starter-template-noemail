"""Batch eval runner.

Reads a seed list of Colombian companies (NIT + name), runs the full
pipeline for each, then diffs the extracted revenue against Supersociedades
ground truth via ``diff_against_sirem``. This is the zero-human-call
validation loop: every company in the seed is Supersociedades-supervised, so
each has a filed income statement to compare against.

Usage:
    python eval/run_batch.py                       # uses eval/colombia_sample.csv
    python eval/run_batch.py eval/colombia_sample.csv --data-dir data

Extraction and tier-2/3 discovery require ANTHROPIC_API_KEY. Without it the
deterministic stages still run (intake, tier-1 acquisition) and the diff
reports each company as not-yet-comparable — useful for validating the
harness and the seed list itself.
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from corporate_profile_agent import pipeline  # noqa: E402
from corporate_profile_agent import tax_ids  # noqa: E402

import diff_against_sirem as differ  # noqa: E402

DEFAULT_SEED = Path(__file__).resolve().parent / "colombia_sample.csv"


def load_seed(path: Path) -> list[dict]:
    with path.open() as fh:
        return list(csv.DictReader(fh))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the batch validation loop.")
    parser.add_argument("seed", nargs="?", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--max-sources", type=int, default=10)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    rows = load_seed(args.seed)
    print(f"seed: {len(rows)} companies from {args.seed}\n")

    generated: list[Path] = []
    for row in rows:
        nit = row["nit"].strip()
        name = row["name"].strip()
        check = tax_ids.validate("CO", nit)
        tag = "valid" if check.valid else f"INVALID ({check.reason})"
        print(f"[{tag:>7}] {nit}  {name[:48]}")
        if not check.valid:
            continue
        try:
            profile, _ = pipeline.run(
                name=name, country="CO", tax_id=nit,
                data_dir=args.data_dir, max_sources=args.max_sources,
            )
        except Exception as exc:
            print(f"          pipeline error: {exc}")
            continue
        profile_path = args.data_dir / check.normalized.replace("/", "_") / "profile.json"
        if profile_path.exists():
            generated.append(profile_path)

    print(f"\n=== validation diff against Supersociedades ground truth ===")
    matched = comparable = 0
    for path in generated:
        nit, ok, detail = differ.evaluate(path)
        marker = "?" if ok is None else "OK" if ok else "MISMATCH"
        print(f"[{marker:>8}] {nit}: {detail}")
        if ok is not None:
            comparable += 1
            matched += int(ok)

    if comparable:
        print(f"\nrevenue field accuracy: {matched}/{comparable} "
              f"({matched / comparable:.0%}) within {differ.TOLERANCE:.0%}")
    else:
        print("\nno comparable profiles yet — set ANTHROPIC_API_KEY to run "
              "discovery + extraction, then re-run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
