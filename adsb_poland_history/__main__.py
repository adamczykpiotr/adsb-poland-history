from pathlib import Path
import os
import argparse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from adsb_poland_history.helpers.downloader import Downloader
from adsb_poland_history.helpers.filesystem import Filesystem
from adsb_poland_history.helpers.github_client import GithubClient
from adsb_poland_history.parsing.entry_parser import EntryParser
from adsb_poland_history.sourcing.adsb_globe_history import AdsbGlobeHistory

github_token = os.getenv("GITHUB_TOKEN")
current_repo_name = "adamczykpiotr/adsb-poland-history"


def process_chunk(file_paths: list[Path], output_dir: Path):
    for file_path in file_paths:
        try:
            parsed = EntryParser.parse_file(file_path)
            if parsed is None:
                continue

            Filesystem.save_entry(parsed, parsed[EntryParser.ICAO_KEY], output_dir)
        finally:
            file_path.unlink(missing_ok=True)


def parse(arguments: argparse.Namespace):
    date = arguments.date  # type: str
    threads = arguments.threads  # type: int

    output_dir = Path("output")
    workdir = Path("workdir")

    github_client = GithubClient()

    # Ensure tag does not already exist
    if github_client.tag_exists(current_repo_name, date):
        raise ValueError(f"Tag for date {date} already exists.")

    # Get source files list
    all_sources = AdsbGlobeHistory(github_client).get_source_files()
    day_source = all_sources.get(date)
    if not day_source:
        raise ValueError(f"No source files found for date {date}.")

    # Download source files
    workdir.mkdir(parents=True, exist_ok=True)
    source_workdir = workdir / "source"
    source_workdir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading source files for date {date}...")
    Downloader.download_and_decompress_tar(day_source, source_workdir)

    traces_path = source_workdir / "traces"
    files = list(Filesystem.get_files_recursively(traces_path))
    print(f"Found {len(files)} files to process.")

    parsed_workdir = workdir / "parsed"
    parsed_workdir.mkdir(parents=True, exist_ok=True)

    # Process files in parallel
    files_chunked = [files[i : i + threads] for i in range(0, len(files), threads)]

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(process_chunk, chunk, parsed_workdir)
            for chunk in files_chunked
        ]

        for future in futures:
            future.result()

    # Compress output to one zip
    print("Compressing parsed files...")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{date}.zip"

    parsed_workdir = parsed_workdir.resolve()
    os.chdir(parsed_workdir)
    os.system(f"zip -qr ../../{output_file} *")

    print("Done!")


def find_missing_dates(arguments: argparse.Namespace):
    year = arguments.year  # type: int | None

    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    delta = timedelta(days=1)

    github_client = GithubClient(github_token)
    existing_tags = github_client.get_all_tags(current_repo_name)
    missing_dates = []
    while start_date <= end_date:
        tag_name = start_date.strftime("%Y-%m-%d")
        if tag_name not in existing_tags:
            missing_dates.append(tag_name)
        start_date += delta

    print(f"Found {len(missing_dates)} missing dates for year {year}.")

    if arguments.limit is not None:
        missing_dates = missing_dates[: arguments.limit]

    print("Dispatching events for missing {len(missing_dates)} dates...")

    for date in missing_dates:
        try:
            github_client.dispatch_event(
                current_repo_name, "trigger-parse-globe-history-date", {"date": date}
            )
        except Exception as e:
            print(f"Failed to dispatch event for {date}: {e}")

    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ADS-B Poland history data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Parse command
    parse_parser = subparsers.add_parser(
        "parse", help="Parse ADS-B data for a given date"
    )
    parse_parser.add_argument("date", type=str, help="Date in YYYY-MM-DD format")
    parse_parser.add_argument(
        "--threads", type=int, default=8, help="Number of threads to use"
    )
    parse_parser.set_defaults(func=parse)

    # Find missing tags command
    find_parser = subparsers.add_parser("handle-missing", help="Handle missing dates")
    find_parser.add_argument("year", default=None, type=int, help="Year to check")
    find_parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of dates to process"
    )
    find_parser.set_defaults(func=find_missing_dates)

    args = parser.parse_args()
    args.func(args)
