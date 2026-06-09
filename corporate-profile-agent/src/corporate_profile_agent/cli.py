"""CLI entry point.

Usage:
    python -m corporate_profile_agent --name "Ecopetrol" --country CO \\
        --tax-id 899999068-1
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="corporate-profile-agent",
        description="Generate an audited corporate profile for a LatAm company.",
    )
    parser.add_argument("--name", required=True, help="Company name")
    parser.add_argument("--country", required=True,
                        help="ISO country code: BR MX CO CL AR PE")
    parser.add_argument("--tax-id", default=None,
                        help="Official ID (CNPJ/RFC/NIT/RUT/CUIT/RUC). "
                             "Strongly recommended — names are ambiguous.")
    parser.add_argument("--data-dir", type=Path, default=None,
                        help="Where to store documents and outputs (default: ./data)")
    parser.add_argument("--max-sources", type=int, default=12)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    profile, report = pipeline.run(
        name=args.name,
        country=args.country,
        tax_id=args.tax_id,
        data_dir=args.data_dir,
        max_sources=args.max_sources,
    )
    print(report)
    return 0 if profile.entity.resolved else 1


if __name__ == "__main__":
    sys.exit(main())
