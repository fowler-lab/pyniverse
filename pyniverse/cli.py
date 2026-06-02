from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from pathlib import Path

import pyniverse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_file",
        required=True,
        help=(
            "The CSV file downloaded from Zooniverse containing all classifications "
            "done to date."
        ),
    )
    parser.add_argument(
        "--output_stem",
        default="test",
        help="The first part of each output filename.",
    )
    parser.add_argument(
        "--output_dir",
        default="graphs",
        help="Directory where generated graph PDFs will be written.",
    )
    parser.add_argument(
        "--from_date",
        default=None,
        help=(
            "If required, only include classifications after this date. Use ISO "
            "format, for example 2017-04-07."
        ),
    )
    parser.add_argument(
        "--to_date",
        default=None,
        help=(
            "If required, only include classifications before this date. Use ISO "
            "format, for example 2017-04-07."
        ),
    )
    parser.add_argument(
        "--timings",
        action="store_true",
        help="Print the time taken for each step.",
    )
    parser.add_argument(
        "--private_project",
        action="store_true",
        help="Do not filter out non-live classifications for private projects.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    options = parser.parse_args(argv)

    print("Reading classifications from CSV file...")
    start = time.time()
    current_classifications = pyniverse.Classifications(
        zooniverse_file=options.input_file,
        from_date=options.from_date,
        to_date=options.to_date,
        live_rows=not options.private_project,
    )
    if options.timings:
        print(f"{time.time() - start:.1f} seconds")

    current_classifications.create_users_table()

    output_dir = Path(options.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for sampling_time in ["month", "week", "day"]:
        current_classifications.plot_classifications_by_time(
            sampling=sampling_time,
            filename=str(
                output_dir
                / f"{options.output_stem}-classifications-{sampling_time}.pdf"
            ),
            add_cumulative=True,
        )
        current_classifications.plot_users_by_time(
            sampling=sampling_time,
            filename=str(
                output_dir / f"{options.output_stem}-users-{sampling_time}.pdf"
            ),
            add_cumulative=True,
        )

    current_classifications.plot_user_classification_distribution(
        filename=str(output_dir / f"{options.output_stem}-user-distribution.pdf")
    )

    print(current_classifications)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
