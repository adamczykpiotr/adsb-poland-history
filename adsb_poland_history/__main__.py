from pathlib import Path
import os
import argparse
from concurrent.futures import ThreadPoolExecutor

from adsb_poland_history.helpers.downloader import Downloader
from adsb_poland_history.helpers.filesystem import Filesystem
from adsb_poland_history.helpers.github_client import GithubClient
from adsb_poland_history.parsing.entry_parser import EntryParser
from adsb_poland_history.sourcing.adsb_globe_history import AdsbGlobeHistory


def process_chunk(file_paths: list[Path], output_dir: Path):
    for file_path in file_paths:
        parsed = EntryParser.parse_file(file_path)
        file_path.unlink(missing_ok=True)

        if parsed is None:
            continue

        Filesystem.save_entry(parsed, parsed[EntryParser.ICAO_KEY], output_dir)


def main(date: str, threads: int):
    output_dir = Path("output")
    workdir = Path("workdir")

    github_client = GithubClient()

    # Ensure tag does not already exist
    if github_client.tag_exists("adsb-poland-history", date):
        raise ValueError(f"Tag for date {date} already exists.")

    # Get source files list
    all_sources = AdsbGlobeHistory(github_client).get_source_files()
    day_source = all_sources.get(date)
    if not day_source:
        raise ValueError(f"No source files found for date {date}")

    # Download source files
    workdir.mkdir(parents=True, exist_ok=True)
    source_workdir = workdir / "source"
    source_workdir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading source files for date {date}...")
    Downloader.download_and_decompress_tar(day_source, source_workdir)

    traces_path = source_workdir / "traces"
    files = list(Filesystem.get_files_recursively(traces_path))
    print(f"Found {len(files)} files to process.")

    # Using a simple thread pool to process files concurrently
    parsed_workdir = workdir / "parsed"
    parsed_workdir.mkdir(parents=True, exist_ok=True)

    # Process files in parallel
    files_chunked = [
        files[i: i + threads] for i in range(0, len(files), threads)
    ]

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(process_chunk, chunk, parsed_workdir)
            for chunk in files_chunked
        ]

        # Wait for all futures to complete
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ADS-B Poland history data.")
    parser.add_argument("date", type=str, help="Date in YYYY-MM-DD format")
    parser.add_argument(
        "--threads",
        type=int,
        default=8,
        help="Number of threads to use for processing files",
    )
    args = parser.parse_args()
    if not args.date:
        raise ValueError("Date argument is required in YYYY-MM-DD format.")
    if args.threads <= 0:
        raise ValueError("Threads argument must be a positive integer.")

    main(args.date, args.threads)
